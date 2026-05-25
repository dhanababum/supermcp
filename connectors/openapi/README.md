# OpenAPI/Swagger MCP Connector

A Model Context Protocol (MCP) connector that converts OpenAPI/Swagger specifications into MCP tool metadata, enabling AI assistants to understand and interact with any API documented in OpenAPI format.

## Features

- **OpenAPI & Swagger Support**: Accept both OpenAPI 3.x and Swagger 2.0 (OpenAPI 3.0) specifications
- **Multiple Input Formats**: Load specs from URLs (JSON/YAML) or paste raw content
- **Spec Validation**: Automatic validation and error reporting for invalid specs
- **Tool Conversion**: Convert OpenAPI operations into MCP-compatible tool definitions
- **Metadata Extraction**: Extract and expose API documentation, parameters, and schemas
- **Flexible Authentication**: Support for various authentication schemes defined in specs

## Architecture

The connector follows the SuperMCP architecture pattern:

```
SuperMCP Dashboard
    ↓ (REST API)
Backend API
    ↓ (MCP Protocol)
OpenAPI Connector (:8034)
    ↓ (HTTP/YAML Parse)
OpenAPI Specification (URL or Raw)
    ↓ (FastMCP Conversion)
MCP Tool Metadata
```

## Configuration

### Configuration Schema

```json
{
  "spec_url": "https://api.example.com/openapi.yaml",
  "timeout": 30,
  "db_name": "my-api"
}
```

**Or:**

```json
{
  "spec_raw": "openapi: 3.0.0\ninfo:\n  title: My API\n  version: 1.0.0\npaths:\n  /users:\n    get:\n      summary: List users",
  "db_name": "my-api"
}
```

**Fields:**

- `spec_url` (optional): Full URL to an OpenAPI/Swagger specification (JSON or YAML)
- `spec_raw` (optional): Raw OpenAPI/Swagger specification content (JSON or YAML string)
- `timeout` (optional, default: 30): HTTP request timeout in seconds (applies when loading from URL)
- `db_name` (optional, default: "default"): Identifier for this OpenAPI connector instance
- `auth_type` (optional, default: "none"): Target API auth method: `none`, `bearer_token`, `api_key`, or `custom_header`
- `auth_token` (optional): Bearer token, API key, or custom header value for target API calls
- `auth_header_name` (optional): Header name for `api_key` or `custom_header`; API keys default to `X-API-Key`

**Note:** Exactly one of `spec_url` or `spec_raw` must be provided.

### JWT Protected Test API

Run the included FastAPI example server:

```bash
cd connectors/openapi
uv run uvicorn example:app --port 9040 --reload
```

Get a JWT:

```bash
curl -X POST http://localhost:9040/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"wonderland"}'
```

Create an OpenAPI connector server with:

```json
{
  "spec_url": "http://localhost:9040/openapi.json",
  "auth_type": "bearer_token",
  "auth_token": "<access_token_from_login>"
}
```

## Installation

### Using Docker (Recommended)

1. **Build the Docker image:**

```bash
cd /path/to/supermcp
docker build -f connectors/openapi/Dockerfile.dev -t openapi-connector:dev .
```

2. **Run the connector:**

```bash
docker run -d \
  --name openapi-connector \
  -p 8034:8034 \
  -e PORT=8034 \
  -e WORKERS=1 \
  openapi-connector:dev
```

### Using UV directly

1. **Install dependencies:**

```bash
cd connectors/openapi
uv sync
```

2. **Run the connector:**

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8034 --reload
```

## Available Tools

### `test_connection()`

Validate the configured OpenAPI source and return specification metadata.

**Returns:**
- `status`: "ok" if validation succeeds
- `source`: Either "url" or "raw" depending on configuration
- `title`: API title from the spec
- `version`: API version from the spec
- `paths`: List of available paths/endpoints

**Example:**
```bash
curl http://localhost:8034/mcp/my-api/tools/test_connection -X POST
```

### `get_openapi_spec()`

Return the full loaded OpenAPI specification.

**Returns:** Complete OpenAPI specification as JSON object

**Example:**
```bash
curl http://localhost:8034/mcp/my-api/tools/get_openapi_spec -X POST
```

### `convert_to_mcp()`

Convert the OpenAPI specification into MCP tool metadata using FastMCP.

**Returns:**
- `name`: Connector/API name
- `version`: API version
- `tool_count`: Number of tools generated
- `tools`: Array of MCP tool definitions

**Example:**
```bash
curl http://localhost:8034/mcp/my-api/tools/convert_to_mcp -X POST
```

## Examples

### From URL

1. Create a connector instance pointing to a Swagger/OpenAPI URL:

```json
{
  "spec_url": "https://petstore.swagger.io/v2/swagger.json"
}
```

2. Call `test_connection()` to verify the spec loads:

```bash
{"status": "ok", "source": "url", "title": "Swagger Petstore", "version": "1.0.0", "paths": ["/pet", "/pet/findByStatus", ...]}
```

3. Call `convert_to_mcp()` to get MCP tools:

```json
{
  "name": "Swagger Petstore",
  "version": "1.0.0",
  "tool_count": 15,
  "tools": [
    {"name": "GET_pet_findByStatus", "description": "Finds Pets by status", "inputSchema": {...}},
    ...
  ]
}
```

### From Raw Content

1. Create a connector instance with raw YAML:

```json
{
  "spec_raw": "openapi: 3.0.0\ninfo:\n  title: Simple API\n  version: 1.0.0\npaths:\n  /hello:\n    get:\n      summary: Say hello"
}
```

2. Call tools to validate and convert the spec

## Testing

Run the test suite with pytest:

```bash
cd connectors/openapi
uv run python3 -m pytest test_main.py
```

Tests verify:
- Configuration validation (requires exactly one spec source)
- Both URL and raw spec acceptance
- Proper error handling for invalid inputs

## Troubleshooting

### "Invalid OpenAPI spec"
- Ensure the spec is valid JSON or YAML
- Check that it contains either `openapi: 3.x.x` or `swagger: 2.0`
- Validate with: `https://editor.swagger.io`

### URL loading fails
- Verify the URL is accessible and returns valid content
- Check network connectivity and HTTPS certificate validity
- Increase timeout if the spec URL is slow to respond

### Tool conversion produces no tools
- Ensure the spec contains at least one path with operations
- Check that paths are properly defined in the `paths` section
- See OpenAPI specification docs: https://spec.openapis.org/

## Related Documentation

- [OpenAPI Specification](https://spec.openapis.org/)
- [Swagger/OpenAPI Editor](https://editor.swagger.io)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP OpenAPI Support](https://github.com/jlowin/fastmcp)

## Port Information

- **Default Port:** 8034
- **Environment Variable:** `PORT`

To run on a different port:

```bash
docker run -e PORT=9999 openapi-connector:dev
```
