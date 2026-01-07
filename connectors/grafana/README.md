# Grafana MCP Connector

A Model Context Protocol (MCP) connector for Grafana that enables AI assistants to interact with Grafana dashboards programmatically.

## Features

- **Dashboard Management**: List, get, create, update, and delete Grafana dashboards
- **Search & Discovery**: Search dashboards by query, tags, or folders
- **Multi-Instance Support**: Connect to multiple Grafana instances with isolated configurations
- **Flexible Authentication**: Support for both Service Account Tokens (Grafana 9.0+) and legacy API Keys
- **Connection Pooling**: Efficient HTTP session management with LRU eviction
- **Template Operations**: Built-in templates for common operations like cloning and backing up dashboards

## Architecture

The connector follows the SuperMCP architecture pattern:

```
SuperMCP Dashboard
    ↓ (REST API)
Backend API
    ↓ (MCP Protocol)
Grafana Connector (:8029)
    ↓ (HTTP/HTTPS)
Grafana API
```

## Configuration

### Authentication Methods

#### Service Account Token (Recommended)

For Grafana 9.0+, use Service Account Tokens:

1. Go to Grafana → Administration → Service Accounts
2. Create a new service account
3. Generate a token with appropriate permissions
4. Use the token in connector configuration

**Required Permissions:**
- `dashboards:read` - View dashboards
- `dashboards:write` - Create/update dashboards
- `dashboards:delete` - Delete dashboards
- `folders:read` - List folders

#### API Key (Legacy)

For older Grafana versions:

1. Go to Grafana → Configuration → API Keys
2. Create a new API key with appropriate role (Admin, Editor, or Viewer)
3. Use the API key in connector configuration

### Configuration Schema

```json
{
  "grafana_url": "https://grafana.example.com",
  "auth_type": "service_account_token",
  "service_account_token": "your_token_here",
  "verify_ssl": true,
  "timeout": 30,
  "db_name": "production-grafana"
}
```

**Fields:**

- `grafana_url` (required): Full URL to your Grafana instance
- `auth_type` (required): Either "service_account_token" or "api_key"
- `service_account_token` (optional): Service account token for authentication
- `api_key` (optional): API key for authentication
- `verify_ssl` (optional, default: true): Verify SSL certificates
- `timeout` (optional, default: 30): Request timeout in seconds
- `additional_params` (optional): Additional HTTP headers as JSON object
- `db_name` (optional, default: "default"): Identifier for this instance

## Installation

### Using Docker (Recommended)

1. **Build the Docker image:**

```bash
cd /path/to/forge-mcptools
docker build -f connectors/grafana/Dockerfile.dev -t grafana-connector:dev .
```

2. **Run the connector:**

```bash
docker run -d \
  --name grafana-connector \
  -p 8029:8029 \
  -e PORT=8029 \
  -e WORKERS=1 \
  grafana-connector:dev
```

### Local Development

1. **Install dependencies:**

```bash
cd connectors/grafana
uv sync
```

2. **Run the connector:**

```bash
uv run python main.py
```

The connector will start on `http://localhost:8029`.

## Available Tools

### Dashboard Management

### list_dashboards()

List all dashboards accessible to the authenticated user.

**Returns:** List of dashboard summaries with uid, title, url, tags, and folder information.

### get_dashboard(uid: str)

Get a specific dashboard by its unique identifier.

**Parameters:**
- `uid`: Dashboard UID

**Returns:** Full dashboard object with metadata and JSON model.

### create_dashboard(dashboard: dict, folder_uid: str = None, message: str = None, overwrite: bool = False)

Create a new dashboard in Grafana.

**Parameters:**
- `dashboard`: Dashboard JSON object (must include "title")
- `folder_uid`: Optional folder UID to create dashboard in
- `message`: Optional commit message
- `overwrite`: Whether to overwrite existing dashboard with same UID

**Returns:** Created dashboard UID, URL, and status.

### update_dashboard(dashboard: dict, overwrite: bool = True, message: str = None)

Update an existing dashboard.

**Parameters:**
- `dashboard`: Dashboard JSON with updated content (must include "uid" and "version")
- `overwrite`: Whether to overwrite the existing dashboard
- `message`: Optional commit message

**Returns:** Updated dashboard UID, URL, version, and status.

### delete_dashboard(uid: str)

Delete a dashboard by its UID.

**Parameters:**
- `uid`: Dashboard UID to delete

**Returns:** Deletion confirmation message.

### search_dashboards(query: str = None, tags: list = None, folder_ids: list = None, limit: int = 100)

Search for dashboards with filters.

**Parameters:**
- `query`: Search query string (searches titles and tags)
- `tags`: List of tags to filter by
- `folder_ids`: List of folder IDs to search in
- `limit`: Maximum number of results (default: 100)

**Returns:** List of matching dashboard summaries.

### get_dashboard_permissions(uid: str)

Get permissions (ACL) for a specific dashboard.

**Parameters:**
- `uid`: Dashboard UID

**Returns:** List of permission entries with user/team access levels.

### Datasource Operations

### get_datasource_by_name(name: str)

Get a datasource by name and return its ID and details.

**Parameters:**
- `name`: Name of the datasource to find

**Returns:** Dictionary with datasource details if found, or error message if not found. Always includes an `exists` boolean field.

**Example Response (found):**
```json
{
  "exists": true,
  "id": 1,
  "uid": "prometheus-uid",
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "isDefault": true
}
```

**Example Response (not found):**
```json
{
  "exists": false,
  "name": "NonExistent",
  "message": "Datasource 'NonExistent' not found"
}
```

### Connection & Health

### test_connection()

Test the connection to Grafana and return status information.

**Returns:** Connection status, health data, organization name, and Grafana version.

## Templates

### clone_dashboard

Clone an existing dashboard with modifications.

**Parameters:**
- `source_uid`: UID of the dashboard to clone
- `new_title`: Title for the cloned dashboard
- `folder_uid`: Optional target folder UID
- `tags`: Optional list of tags for the cloned dashboard

**Example:**
```json
{
  "source_uid": "abc123",
  "new_title": "Dashboard Clone",
  "folder_uid": "folder_xyz",
  "tags": ["clone", "test"]
}
```

### backup_dashboard

Export a dashboard as JSON for backup purposes.

**Parameters:**
- `uid`: UID of the dashboard to backup
- `include_metadata`: Whether to include metadata (default: true)

**Example:**
```json
{
  "uid": "abc123",
  "include_metadata": true
}
```

## Usage Examples

### Example: List All Dashboards

```python
# Using MCP protocol
result = await connector.call_tool("list_dashboards", {})
dashboards = result["content"]
```

### Example: Create a Simple Dashboard

```python
dashboard = {
    "title": "My New Dashboard",
    "tags": ["automated", "test"],
    "timezone": "browser",
    "panels": [],
    "schemaVersion": 36
}

result = await connector.call_tool("create_dashboard", {
    "dashboard": dashboard,
    "folder_uid": "general",
    "message": "Created via MCP"
})
```

### Example: Clone a Dashboard

```python
result = await connector.call_tool("clone_dashboard", {
    "source_uid": "original_dashboard_uid",
    "new_title": "Cloned Dashboard",
    "tags": ["clone"]
})
```

### Example: Search Dashboards

```python
result = await connector.call_tool("search_dashboards", {
    "query": "production",
    "tags": ["monitoring"],
    "limit": 50
})
```

### Example: Get Datasource by Name

```python
# Check if datasource exists and get its ID
result = await connector.call_tool("get_datasource_by_name", {
    "name": "Prometheus"
})

if result["exists"]:
    datasource_id = result["id"]
    datasource_uid = result["uid"]
    print(f"Found datasource: {datasource_id} ({datasource_uid})")
else:
    print(f"Datasource not found: {result['message']}")
```

## Testing

### Run Unit Tests

```bash
cd connectors/grafana
uv run pytest
```

### Run Specific Test File

```bash
uv run pytest test_session_manager.py -v
```

### Run Tests with Coverage

```bash
uv run pytest --cov=. --cov-report=html
```

## SSL/TLS Configuration

### Self-Signed Certificates

For testing with self-signed certificates:

```json
{
  "grafana_url": "https://grafana.local",
  "verify_ssl": false,
  "auth_type": "service_account_token",
  "service_account_token": "your_token"
}
```

**⚠️ Warning:** Disabling SSL verification is not recommended for production environments.

### Custom CA Certificates

For custom CA certificates, you can add them to the Docker container or system trust store.

## Troubleshooting

### Connection Refused

**Issue:** Unable to connect to Grafana instance.

**Solutions:**
1. Verify the `grafana_url` is correct and accessible
2. Check network connectivity
3. Ensure Grafana is running and accepting connections
4. Check firewall rules

### Authentication Failed (401)

**Issue:** "Authentication failed. Please check your credentials."

**Solutions:**
1. Verify the token/API key is correct
2. Check that the token hasn't expired
3. Ensure the service account or API key has required permissions
4. For service accounts, verify Grafana version is 9.0+

### Permission Denied (403)

**Issue:** "Permission denied. Insufficient privileges."

**Solutions:**
1. Check service account permissions
2. For API keys, ensure the role (Viewer/Editor/Admin) is appropriate
3. Verify folder permissions if creating dashboards in specific folders

### Dashboard Not Found (404)

**Issue:** "Resource not found for operation: get dashboard"

**Solutions:**
1. Verify the dashboard UID is correct
2. Check that the dashboard exists in Grafana
3. Ensure the authenticated user has access to the dashboard

### Version Conflict (412)

**Issue:** "Version conflict. The dashboard has been modified by another user."

**Solutions:**
1. Retrieve the latest version of the dashboard
2. Update the `version` field in your dashboard JSON
3. Set `overwrite: true` to force overwrite (use with caution)

## Performance Tuning

### Session Pool Configuration

The connector uses session pooling to manage HTTP connections efficiently. You can adjust the pool settings by modifying the SessionManager initialization in `main.py`:

```python
session_manager = SessionManager(
    global_max_sessions=100,  # Total sessions across all servers
    per_target_max=10,        # Max sessions per Grafana instance
    idle_ttl=300              # Idle timeout in seconds
)
```

### Request Timeout

Adjust the timeout for slow Grafana instances:

```json
{
  "timeout": 60
}
```

## Security Best Practices

1. **Use Service Account Tokens** instead of API Keys when possible
2. **Enable SSL verification** in production environments
3. **Limit permissions** - grant only necessary permissions to service accounts
4. **Rotate credentials** regularly
5. **Use environment variables** for sensitive data instead of hardcoding
6. **Monitor access logs** in Grafana for suspicious activity

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `uv run pytest`
2. Code follows existing patterns
3. New features include tests
4. Documentation is updated

## License

This connector is part of the SuperMCP project and follows the project's license terms.

## Support

For issues, questions, or contributions:

- GitHub Issues: [SuperMCP Issues](https://github.com/dhanababum/supermcp/issues)
- Documentation: [SuperMCP Docs](https://docs.supermcp.com)

## Version History

### 1.0.0 (Initial Release)
- Dashboard management (list, get, create, update, delete)
- Search functionality
- Service Account Token and API Key authentication
- Connection pooling
- Clone and backup templates
- Docker support

