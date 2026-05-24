"""OpenAPI MCP Connector - Main Entry Point"""

import json
import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx
import yaml
from fastmcp.server.providers.openapi import OpenAPIProvider
from mcp_pkg.dynamic_mcp import (
    create_dynamic_mcp,
    get_current_server_config,
    get_current_server_id,
)

from schema import AuthType, OpenAPIConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp, app = create_dynamic_mcp(
    name="openapi",
    config=OpenAPIConfig,
    version="1.0.0",
    logo_file_path=os.path.join(
        os.path.dirname(__file__), "media/openapi-48.png"
    ),
    stateless_http=True,
)

ui_schema = {
    "spec_url": {
        "ui:widget": "text",
        "ui:placeholder": "https://example.com/openapi.yaml",
        "ui:help": "URL to the Swagger/OpenAPI JSON or YAML definition",
    },
    "spec_raw": {
        "ui:widget": "textarea",
        "ui:options": {"rows": 12},
        "ui:placeholder": "Paste the OpenAPI JSON or YAML here",
        "ui:help": "Raw OpenAPI or Swagger spec content",
    },
    "timeout": {
        "ui:widget": "updown",
        "ui:help": "Request timeout in seconds when loading the spec URL",
    },
    "auth_type": {
        "ui:widget": "select",
        "ui:help": "Authentication method for calls to the target API",
    },
    "auth_token": {
        "ui:widget": "password",
        "ui:help": "Bearer token, API key, or custom header value",
    },
    "auth_header_name": {
        "ui:widget": "text",
        "ui:placeholder": "X-API-Key",
        "ui:help": "Header name for API key or custom header auth",
    },
}

mcp.register_ui_schema(ui_schema)

loaded_specs: Dict[str, Dict[str, Any]] = {}
openapi_clients: Dict[str, httpx.AsyncClient] = {}


def _runtime_namespace(server_id: str) -> str:
    return f"server_{server_id.replace('-', '_')}"


def _create_openapi_client(
    openapi_spec: Dict[str, Any],
    timeout: int,
    spec_url: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> httpx.AsyncClient:
    client_kwargs = {"timeout": timeout, "headers": headers or {}}
    servers = openapi_spec.get("servers") or []
    if servers and servers[0].get("url"):
        base_url = servers[0]["url"]
        for name, var in servers[0].get("variables", {}).items():
            base_url = base_url.replace(f"{{{name}}}", var.get("default", ""))
        return httpx.AsyncClient(base_url=base_url, **client_kwargs)

    if openapi_spec.get("swagger") == "2.0" and openapi_spec.get("host"):
        scheme = (openapi_spec.get("schemes") or ["https"])[0]
        base_path = openapi_spec.get("basePath") or ""
        return httpx.AsyncClient(
            base_url=f"{scheme}://{openapi_spec['host']}{base_path}",
            **client_kwargs,
        )

    if spec_url:
        parsed = urlsplit(spec_url)
        if parsed.scheme and parsed.netloc:
            base_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
            return httpx.AsyncClient(base_url=base_url, **client_kwargs)

    raise ValueError(
        "OpenAPI spec must define servers[0].url, Swagger 2.0 host/basePath, "
        "or be loaded from spec_url"
    )


def _auth_headers(server_config: OpenAPIConfig) -> Dict[str, str]:
    if server_config.auth_type == AuthType.none or not server_config.auth_token:
        return {}
    if server_config.auth_type == AuthType.bearer_token:
        return {"Authorization": f"Bearer {server_config.auth_token}"}
    if server_config.auth_type == AuthType.api_key:
        header_name = server_config.auth_header_name or "X-API-Key"
        return {header_name: server_config.auth_token}
    if server_config.auth_type == AuthType.custom_header:
        return {server_config.auth_header_name: server_config.auth_token}
    return {}


async def _load_openapi_spec(server_config: OpenAPIConfig) -> Dict[str, Any]:
    """Load OpenAPI/Swagger spec from URL or raw text."""
    try:
        if server_config.spec_url:
            async with httpx.AsyncClient(timeout=server_config.timeout) as client:
                response = await client.get(server_config.spec_url)
                response.raise_for_status()
                content = response.text
        else:
            content = server_config.spec_raw or ""

        if not content.strip():
            raise ValueError("OpenAPI spec content is empty")

        try:
            openapi_spec = json.loads(content)
        except json.JSONDecodeError:
            openapi_spec = yaml.safe_load(content)

        if not isinstance(openapi_spec, dict):
            raise ValueError("OpenAPI spec must be a JSON or YAML object")

        if "openapi" not in openapi_spec and "swagger" not in openapi_spec:
            raise ValueError("Spec is not a valid OpenAPI or Swagger document")

        return openapi_spec
    except Exception as exc:
        logger.error("Failed to load OpenAPI spec: %s", exc)
        raise


@mcp.on_server_create()
async def on_server_start(server_id: str, server_config: OpenAPIConfig):
    """Load the OpenAPI spec and expose its operations for this server."""
    logger.info("Loading OpenAPI spec for server %s", server_id)
    openapi_spec = await _load_openapi_spec(server_config)
    loaded_specs[server_id] = openapi_spec
    info = openapi_spec.get("info", {})
    logger.info(
        "Loaded OpenAPI document %s version %s",
        info.get("title"),
        info.get("version"),
    )

    await _close_openapi_client(server_id)
    client = _create_openapi_client(
        openapi_spec,
        server_config.timeout,
        server_config.spec_url,
        _auth_headers(server_config),
    )
    provider = OpenAPIProvider(openapi_spec=openapi_spec, client=client)
    namespace = _runtime_namespace(server_id)
    public_tools = await provider.list_tools()
    mcp.add_provider(provider, namespace=namespace)
    openapi_clients[server_id] = client

    result = {
        "tools": [
            {
                "tool": tool.to_mcp_tool().model_dump(),
                "template_args": {
                    "runtime_tool_name": f"{namespace}_{tool.name}",
                },
            }
            for tool in public_tools
        ]
    }
    print(result)
    return result


@mcp.on_server_destroy()
async def on_server_stop(server_id: str):
    """Cleanup the cached OpenAPI spec when the connector server stops."""
    loaded_specs.pop(server_id, None)
    await _close_openapi_client(server_id)
    logger.info("Cleared OpenAPI spec cache for server %s", server_id)


async def _close_openapi_client(server_id: str):
    client = openapi_clients.pop(server_id, None)
    if client:
        await client.aclose()


@mcp.tool()
async def test_connection() -> Dict[str, Any]:
    """Validate the configured OpenAPI source and return spec metadata."""
    server_id = get_current_server_id()
    server_config = get_current_server_config(app, server_id)
    openapi_spec = await _load_openapi_spec(server_config)
    info = openapi_spec.get("info", {})
    return {
        "status": "ok",
        "source": "url" if server_config.spec_url else "raw",
        "title": info.get("title"),
        "version": info.get("version"),
        "paths": list(openapi_spec.get("paths", {}).keys()),
    }
