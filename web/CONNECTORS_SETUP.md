# Connectors Feature Setup Guide

## Overview

The Connectors feature has been successfully added to the dashboard! Here's what was implemented:

### Features Added

1. **New "Connectors" Menu Item** - Added to the sidebar navigation (third item)
2. **Connectors Page** - Beautiful grid layout displaying all available connectors
3. **Real-time Data** - Fetches connectors from your FastAPI backend
4. **Search & Filter** - Search bar and filter button for future enhancements
5. **Action Buttons** - Add Connector, Refresh, and Configure buttons
6. **Status Indicators** - Visual badges showing connector status
7. **Responsive Grid** - Adapts to mobile, tablet, and desktop screens
8. **Loading States** - Spinner while fetching data
9. **Error Handling** - Friendly error messages if API is unavailable
10. **Empty State** - Beautiful placeholder when no connectors exist

## How to Test

### Step 1: Start the FastAPI Backend

Open a new terminal and run:

```bash
cd /Users/dhanababu/workspace/forge-mcptools
python api/main.py
```

The API server will start on `http://localhost:9000`

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9000
```

### Step 2: Verify Backend is Running

Test the API endpoint in another terminal:

```bash
curl http://localhost:9000/api/connectors
```

You should see:
```json
[
  {
    "sql_db": {
      "name": "SQL databases",
      "description": "Connect to SQL databases",
      "version": "0.1.0",
      "author": "MCP Tools"
    }
  }
]
```

### Step 3: View the React Dashboard

The React app should already be running at `http://localhost:3000`

If not, start it:

```bash
cd /Users/dhanababu/workspace/forge-mcptools/web
npm start
```

### Step 4: Navigate to Connectors

1. Open `http://localhost:3000` in your browser
2. Click on **"Connectors"** in the sidebar (third menu item)
3. You should see the SQL databases connector displayed in a card with:
   - Connector icon and name
   - Description
   - Version and author info
   - "Active" status badge
   - Configure button

## Architecture

### Frontend (React + Tailwind)
- **File**: `/web/src/App.js`
- **State Management**: React hooks (useState, useEffect)
- **Styling**: Tailwind CSS utility classes
- **API Call**: Fetch API to `http://localhost:9000/api/connectors`

### Backend (FastAPI)
- **File**: `/api/main.py`
- **Endpoint**: `GET /api/connectors`
- **Port**: 9000
- **Response**: Array of connector objects

### Data Flow

```
User clicks "Connectors" 
  → useEffect triggers
    → Fetch GET /api/connectors
      → Backend returns connector data
        → Frontend updates state
          → Grid renders connector cards
```

## Connector Card Features

Each connector card displays:
- **Icon**: Gradient purple-to-blue background with database icon
- **Status Badge**: Green "Active" badge
- **Name**: Connector display name
- **Description**: Brief description of what it connects to
- **Metadata**: Version and author information
- **Actions**:
  - "Configure" button (primary action)
  - "..." menu button (more options)

## Adding More Connectors

To add more connectors, update the `get_all_connectors()` function in:
`/Users/dhanababu/workspace/forge-mcptools/mcp_tools/connectors/__init__.py`

Example:
```python
def get_all_connectors():
    return [
        {
            "sql_db": {
                "name": "SQL databases",
                "description": "Connect to SQL databases",
                "version": "0.1.0",
                "author": "MCP Tools",
            }
        },
        {
            "rest_api": {
                "name": "REST APIs",
                "description": "Connect to REST API endpoints",
                "version": "0.1.0",
                "author": "MCP Tools",
            }
        }
    ]
```

## Troubleshooting

### Error: "Failed to fetch connectors"

**Problem**: Cannot connect to backend API

**Solutions**:
1. Verify API server is running: `curl http://localhost:9000/api/connectors`
2. Check the port (default: 9000)
3. Look for CORS errors in browser console

### Empty Grid

**Problem**: No connectors displayed

**Check**:
1. API is returning data: `curl http://localhost:9000/api/connectors`
2. Browser console for errors (F12)
3. Network tab shows successful API call

### Port Already in Use

**Problem**: Port 9000 already taken

**Solution**:
```bash
# Find process using port 9000
lsof -i :9000

# Kill the process or change port in api/main.py
uvicorn.run(app, host="0.0.0.0", port=9001)

# Update frontend API URL in web/src/App.js
fetch('http://localhost:9001/api/connectors')
```

## Future Enhancements

- [ ] Add connector search functionality
- [ ] Implement filter by status/type
- [ ] Add pagination for many connectors
- [ ] Connector configuration modal
- [ ] Add new connector form
- [ ] Edit/delete connector actions
- [ ] Connector health checks
- [ ] Connection testing
- [ ] Activity logs per connector

## UI Components Used

- **Grid Layout**: Tailwind `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- **Cards**: White background with border and hover shadow
- **Buttons**: Purple primary buttons with hover states
- **Icons**: Inline SVG components (Heroicons style)
- **Loading**: Spinning circle animation
- **Empty State**: Dashed border card with CTA

Enjoy your new Connectors feature! 🚀


