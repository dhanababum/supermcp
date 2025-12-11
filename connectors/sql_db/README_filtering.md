# MCP Server with User-Based Tool Filtering

This MCP server demonstrates how to filter tools based on authenticated users using JWT tokens.

## Features

- **JWT Authentication**: Uses RSA key pairs for secure token verification
- **User-Based Tool Filtering**: Only shows tools that belong to the authenticated user
- **Middleware-Based Security**: Implements filtering at both tool listing and tool calling levels
- **Backward Compatibility**: Supports both JWT and simple token-based authentication

## How It Works

### 1. Tool Naming Convention
Tools are named with the pattern: `{user_id}__{tool_name}`

Examples:
- `test-user-123__echo` - Echo tool for user "test-user-123"
- `alice__whoami` - Whoami tool for user "alice"
- `bob__sum` - Sum tool for user "bob"

### 2. Authentication Methods

#### JWT Authentication (Primary)
- Uses RSA key pairs for signing and verification
- User ID is extracted from the JWT `sub` (subject) field
- Token includes scopes: `["read", "write", "admin"]`

#### Simple Token Authentication (Fallback)
- Uses simple bearer tokens for backward compatibility
- Maps tokens to users via the `TOKENS` dictionary

### 3. Filtering Logic

#### Tool Listing (`on_list_tools`)
1. Extracts user ID from JWT token or Authorization header
2. If no user found, returns empty tool list
3. Filters tools to only include those prefixed with `{user_id}__`
4. Returns filtered tool list

#### Tool Calling (`on_call_tool`)
1. Extracts user ID from JWT token or Authorization header
2. Validates that the requested tool name starts with `{user_id}__`
3. Rejects calls to tools that don't belong to the user
4. Allows calls to proceed if ownership is verified

## Usage

### 1. Start the Server
```bash
python new_mcp.py
```

The server will:
- Generate an RSA key pair
- Create a test JWT token
- Start the MCP server on `http://127.0.0.1:8015/mcp`

### 2. Test the Filtering
```bash
python test_filtering.py
```

This will test:
- Tool listing with JWT authentication
- Tool calling with JWT authentication
- Unauthorized access (should return no tools)

### 3. Manual Testing

#### List Tools
```bash
curl -X POST http://127.0.0.1:8015/mcp \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

#### Call a Tool
```bash
curl -X POST http://127.0.0.1:8015/mcp \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "test-user-123__echo",
      "arguments": {
        "payload": {"message": "Hello!"}
      }
    }
  }'
```

## Security Features

1. **JWT Verification**: Validates token signature and expiration
2. **User Isolation**: Users can only see and call their own tools
3. **No Cross-User Access**: Attempts to call another user's tools are rejected
4. **Unauthorized Access**: Returns empty tool list for unauthenticated requests

## Configuration

### JWT Settings
- **Issuer**: `https://test.yourcompany.com`
- **Audience**: `test-mcp-server`
- **Scopes**: `["read", "write", "admin"]`
- **Algorithm**: RS256 (RSA with SHA-256)

### Server Settings
- **Host**: `127.0.0.1`
- **Port**: `8015`
- **Path**: `/mcp`

## Debugging

The server includes extensive logging to help debug authentication and filtering:

- Tool listing requests and responses
- User extraction from JWT tokens
- Tool filtering results
- Tool call authorization decisions

Check the server console output for detailed logs.

## Extending

To add new users and tools:

1. **Add JWT User**: Generate a new JWT token with the desired `sub` field
2. **Register Tools**: Use `register_owner_tool(user_id, tool_name, function, description)`
3. **Test**: Verify the user can only see their own tools

Example:
```python
# Add tools for a new user
register_owner_tool("new-user-456", "custom_tool", my_function, "Custom tool description")
```
