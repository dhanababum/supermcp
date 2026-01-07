# Grafana Connector - Integration Testing Guide

## Overview

The Grafana MCP connector has been fully implemented and is ready for integration testing with the SuperMCP platform. All core functionality has been developed and tested.

## What Was Completed

✅ **Core Implementation**
- [x] Configuration schema with GrafanaConfig and parameter models
- [x] Session manager with HTTP connection pooling
- [x] Main entry point with all tools and lifecycle hooks
- [x] Docker support (Dockerfile.dev, entrypoint.sh)
- [x] Complete test suite with unit tests
- [x] Comprehensive documentation (README.md)

✅ **Tools Implemented**
- [x] `list_dashboards()` - List all accessible dashboards
- [x] `get_dashboard(uid)` - Get dashboard by UID
- [x] `create_dashboard()` - Create new dashboard
- [x] `update_dashboard()` - Update existing dashboard
- [x] `delete_dashboard(uid)` - Delete dashboard
- [x] `search_dashboards()` - Search with filters
- [x] `get_dashboard_permissions(uid)` - Get dashboard ACL
- [x] `test_connection()` - Verify Grafana connectivity

✅ **Templates Implemented**
- [x] `clone_dashboard` - Clone dashboard with modifications
- [x] `backup_dashboard` - Export dashboard JSON

## Prerequisites for Integration Testing

### 1. Environment Configuration

The connector requires the following environment variables to run (set by SuperMCP backend):

```bash
APP_BASE_URL=http://localhost:9000          # SuperMCP backend URL
ORIGIN_URLS=http://localhost:3000           # Frontend URL for CORS
CONNECTOR_SECRET=<secret_from_backend>       # Connector authentication secret
CONNECTOR_ID=<uuid_from_backend>             # Connector UUID
PORT=8029                                    # Connector port (default)
WORKERS=1                                    # Number of workers
```

### 2. Grafana Instance

You need a running Grafana instance for testing. Options:

**Option A: Local Grafana with Docker**
```bash
docker run -d -p 3000:3000 \
  --name=grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  grafana/grafana:latest
```

Access at: http://localhost:3000 (admin/admin)

**Option B: Grafana Cloud**
- Use an existing Grafana Cloud instance
- Create a service account token with dashboard permissions

## Integration Testing Steps

### Step 1: Register Connector in SuperMCP

1. **Start SuperMCP Backend**
   ```bash
   cd app
   uv run python src/main.py
   ```

2. **Access Dashboard**
   - Open http://localhost:3000
   - Navigate to Connectors section

3. **Add Grafana Connector**
   - The connector should auto-register when started
   - Or manually add: http://localhost:8029/connector.json

### Step 2: Start Grafana Connector

With the environment variables set by SuperMCP:

```bash
cd connectors/grafana
PORT=8029 uv run python main.py
```

Or using Docker:

```bash
docker build -f Dockerfile.dev -t grafana-connector:dev .
docker run -p 8029:8029 \
  -e APP_BASE_URL=http://host.docker.internal:9000 \
  -e CONNECTOR_SECRET=<secret> \
  -e CONNECTOR_ID=<uuid> \
  grafana-connector:dev
```

### Step 3: Create Server Instance

1. **In SuperMCP Dashboard**:
   - Click "Create Server" for Grafana connector
   - Fill in configuration:
     ```json
     {
       "grafana_url": "http://localhost:3000",
       "auth_type": "service_account_token",
       "service_account_token": "<your_token>",
       "verify_ssl": false,
       "db_name": "local-grafana"
     }
     ```

2. **Create Service Account Token in Grafana**:
   - Go to Administration → Service Accounts
   - Create new service account
   - Generate token with permissions:
     - `dashboards:read`
     - `dashboards:write`
     - `dashboards:delete`
     - `folders:read`

### Step 4: Test Tools

Test each tool through the SuperMCP dashboard:

1. **Test Connection**
   ```json
   Tool: test_connection
   Parameters: {}
   Expected: Connection status with Grafana version
   ```

2. **List Dashboards**
   ```json
   Tool: list_dashboards
   Parameters: {}
   Expected: Array of dashboard summaries
   ```

3. **Get Dashboard**
   ```json
   Tool: get_dashboard
   Parameters: {"uid": "<dashboard_uid>"}
   Expected: Full dashboard object with metadata
   ```

4. **Create Dashboard**
   ```json
   Tool: create_dashboard
   Parameters: {
     "dashboard": {
       "title": "Test Dashboard",
       "panels": [],
       "tags": ["test"]
     },
     "message": "Created via MCP"
   }
   Expected: New dashboard UID and URL
   ```

5. **Search Dashboards**
   ```json
   Tool: search_dashboards
   Parameters: {
     "query": "test",
     "limit": 10
   }
   Expected: Filtered dashboard list
   ```

6. **Clone Dashboard**
   ```json
   Template: clone_dashboard
   Parameters: {
     "source_uid": "<existing_uid>",
     "new_title": "Cloned Dashboard"
   }
   Expected: New dashboard created with cloned content
   ```

## Validation Checklist

### Functional Tests
- [ ] Connector appears in SuperMCP dashboard
- [ ] Configuration form renders with all fields
- [ ] Can create server instance with valid credentials
- [ ] `test_connection` returns success for valid config
- [ ] Can list dashboards from Grafana
- [ ] Can get individual dashboard details
- [ ] Can create new dashboard
- [ ] Can update existing dashboard
- [ ] Can delete dashboard
- [ ] Can search dashboards with filters
- [ ] Can view dashboard permissions
- [ ] Clone template works correctly
- [ ] Backup template exports dashboard JSON

### Error Handling Tests
- [ ] Invalid credentials return 401 error
- [ ] Invalid dashboard UID returns 404
- [ ] Missing required fields return validation errors
- [ ] Connection timeout handled gracefully
- [ ] SSL verification errors reported clearly

### Performance Tests
- [ ] Multiple concurrent requests handled
- [ ] Session pooling working (check logs)
- [ ] Idle sessions cleaned up after TTL
- [ ] Multiple server instances work independently

### Security Tests
- [ ] Credentials not logged or exposed
- [ ] SSL verification works when enabled
- [ ] Authentication required for all operations
- [ ] Proper authorization checks in Grafana

## Expected Results

### Successful Integration
- Connector starts without errors
- Appears in connector list with Grafana logo
- Configuration form is user-friendly
- All tools execute successfully
- Error messages are clear and actionable
- Performance is acceptable (<1s per request)

### Common Issues and Solutions

**Issue**: "service_account_token is required"
- **Solution**: Ensure auth_type matches the credential provided

**Issue**: "Connection refused"
- **Solution**: Verify grafana_url is correct and accessible

**Issue**: "Authentication failed (401)"
- **Solution**: Verify token is valid and not expired

**Issue**: "Permission denied (403)"
- **Solution**: Check service account has required permissions

**Issue**: "Version conflict (412)"
- **Solution**: Retrieve latest dashboard version before updating

## Next Steps After Integration

1. **Monitor Production Usage**
   - Check logs for errors
   - Monitor performance metrics
   - Collect user feedback

2. **Future Enhancements**
   - Add support for folders management
   - Implement datasource operations
   - Add alerting rules management
   - Support for annotations
   - Snapshot operations

3. **Documentation Updates**
   - Add real-world usage examples
   - Create video tutorials
   - Document common workflows
   - Add troubleshooting guide

## Support

If issues arise during integration testing:

1. **Check Logs**:
   ```bash
   # Connector logs
   cd connectors/grafana
   tail -f logs/connector.log
   
   # Backend logs
   cd app
   tail -f logs/backend.log
   ```

2. **Enable Debug Mode**:
   Set environment variable: `DEBUG=true`

3. **Test Components Independently**:
   - Test Grafana API directly with curl
   - Test connector health endpoint: `curl http://localhost:8029/health`
   - Verify backend can reach connector

4. **Contact Support**:
   - GitHub Issues: [SuperMCP Issues](https://github.com/dhanababum/supermcp/issues)
   - Include logs and error messages

## Conclusion

The Grafana MCP connector is fully implemented and ready for integration testing. All code is complete, tested, and documented. The connector follows SuperMCP patterns and is consistent with the existing postgres and mssql connectors.

**Status**: ✅ Ready for Integration Testing
**Port**: 8029
**Version**: 1.0.0
**Last Updated**: December 2025



