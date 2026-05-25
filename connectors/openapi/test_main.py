import pytest

from main import _auth_headers, _create_openapi_client, _runtime_namespace, on_server_start
from schema import AuthType, OpenAPIConfig


def test_openapi_config_requires_one_source():
    with pytest.raises(ValueError):
        OpenAPIConfig()


def test_openapi_config_rejects_both_sources():
    with pytest.raises(ValueError):
        OpenAPIConfig(spec_url="https://example.com/openapi.yaml", spec_raw="{}")


def test_openapi_config_accepts_raw_spec():
    config = OpenAPIConfig(
        spec_raw=(
            "openapi: 3.0.0\ninfo:\n  title: test\n"
            "  version: 1.0\npaths: {}"
        )
    )
    assert config.spec_raw is not None
    assert config.spec_url is None


def test_runtime_namespace_is_tool_name_safe():
    assert _runtime_namespace("abc-def") == "server_abc_def"


def test_create_openapi_client_supports_swagger_2_base_url():
    client = _create_openapi_client(
        {
            "swagger": "2.0",
            "info": {"title": "test", "version": "1.0"},
            "host": "api.example.com",
            "basePath": "/v1",
            "schemes": ["https"],
            "paths": {},
        },
        timeout=9,
    )
    try:
        assert str(client.base_url) == "https://api.example.com/v1/"
        assert client.timeout.connect == 9
    finally:
        import anyio

        anyio.run(client.aclose)


def test_create_openapi_client_falls_back_to_spec_url_origin():
    client = _create_openapi_client(
        {
            "openapi": "3.0.0",
            "info": {"title": "test", "version": "1.0"},
            "paths": {},
        },
        timeout=9,
        spec_url="http://localhost:9000/openapi.json",
    )
    try:
        assert str(client.base_url).rstrip("/") == "http://localhost:9000"
    finally:
        import anyio

        anyio.run(client.aclose)


def test_auth_headers_support_bearer_api_key_and_custom_header():
    assert _auth_headers(
        OpenAPIConfig(
            spec_raw="openapi: 3.0.0\ninfo:\n  title: test\n  version: 1\npaths: {}",
            auth_type=AuthType.bearer_token,
            auth_token="jwt-token",
        )
    ) == {"Authorization": "Bearer jwt-token"}

    assert _auth_headers(
        OpenAPIConfig(
            spec_raw="openapi: 3.0.0\ninfo:\n  title: test\n  version: 1\npaths: {}",
            auth_type=AuthType.api_key,
            auth_token="api-key",
        )
    ) == {"X-API-Key": "api-key"}

    assert _auth_headers(
        OpenAPIConfig(
            spec_raw="openapi: 3.0.0\ninfo:\n  title: test\n  version: 1\npaths: {}",
            auth_type=AuthType.custom_header,
            auth_token="secret",
            auth_header_name="X-Custom-Auth",
        )
    ) == {"X-Custom-Auth": "secret"}


def test_openapi_config_requires_auth_token_when_auth_enabled():
    with pytest.raises(ValueError):
        OpenAPIConfig(
            spec_raw="openapi: 3.0.0\ninfo:\n  title: test\n  version: 1\npaths: {}",
            auth_type=AuthType.bearer_token,
        )


@pytest.mark.anyio
async def test_server_create_returns_openapi_dynamic_tools():
    config = OpenAPIConfig(
        spec_raw="""
openapi: 3.0.0
info:
  title: Simple API
  version: 1.0.0
servers:
  - url: https://api.example.com
paths:
  /hello:
    get:
      operationId: sayHello
      summary: Say hello
      responses:
        '200':
          description: ok
"""
    )

    result = await on_server_start("abc-def", config)
    try:
        assert len(result["tools"]) == 1
        assert result["tools"][0]["tool"]["name"] == "sayHello"
        assert (
            result["tools"][0]["template_args"]["runtime_tool_name"]
            == "server_abc_def_sayHello"
        )
        from main import mcp

        assert await mcp.get_tool("server_abc_def_sayHello") is not None
    finally:
        from main import on_server_stop

        await on_server_stop("abc-def")
