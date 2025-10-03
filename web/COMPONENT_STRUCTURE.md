# Web Application Component Structure

This document describes the refactored component structure for improved code readability and maintainability.

## Directory Structure

```
web/src/
├── App.js                          # Main application component (simplified)
├── index.js                        # Application entry point
├── index.css                       # Global styles
├── components/                     # Reusable UI components
│   ├── layout/                     # Layout components
│   │   ├── Sidebar.jsx            # Sidebar navigation
│   │   ├── Header.jsx             # Top header bar
│   │   ├── Banner.jsx             # Promotional banner
│   │   └── index.js               # Layout exports
│   ├── common/                     # Common/shared components
│   │   ├── LoadingSpinner.jsx     # Loading state component
│   │   ├── ErrorMessage.jsx       # Error display component
│   │   └── index.js               # Common exports
│   └── icons/                      # SVG icon components
│       └── index.js                # All icon exports
├── pages/                          # Page-level components
│   ├── Dashboard/                  # Dashboard page
│   │   ├── Dashboard.jsx          # Main dashboard component
│   │   ├── components/            # Dashboard-specific components
│   │   │   ├── CompanyStats.jsx
│   │   │   ├── OwnershipChart.jsx
│   │   │   ├── ActivityPanel.jsx
│   │   │   ├── FundingRounds.jsx
│   │   │   ├── TotalOptions.jsx
│   │   │   └── index.js
│   │   └── index.js
│   ├── Connectors/                 # Connectors page
│   │   ├── Connectors.jsx         # Main connectors component
│   │   ├── components/            # Connector-specific components
│   │   │   ├── ConnectorCard.jsx
│   │   │   ├── ConfigurationModal.jsx
│   │   │   └── index.js
│   │   └── index.js
│   ├── Servers/                    # Servers page
│   │   ├── Servers.jsx            # Main servers component
│   │   ├── components/            # Server-specific components
│   │   │   ├── ServerTable.jsx
│   │   │   └── index.js
│   │   └── index.js
│   ├── ServerTools/                # Server Tools page
│   │   ├── ServerTools.jsx        # Main server tools component
│   │   ├── components/            # Tool-specific components
│   │   │   ├── ToolsList.jsx
│   │   │   ├── ToolDetails.jsx
│   │   │   └── index.js
│   │   └── index.js
│   └── index.js                    # Pages exports
├── services/                       # API service layer
│   └── api.js                      # API calls and utilities
├── hooks/                          # Custom React hooks
│   ├── useConnectors.js           # Connectors data hook
│   ├── useServers.js              # Servers data hook
│   ├── useServerTools.js          # Server tools data hook
│   └── index.js                    # Hooks exports
└── constants/                      # Application constants
    └── navigation.js               # Navigation configuration
```

## Architecture Principles

### 1. **Feature-Based Organization**
Each page has its own directory containing:
- Main page component
- Page-specific subcomponents
- Index file for clean exports

### 2. **Component Hierarchy**
```
App.js (Root)
├── Layout Components (Sidebar, Header, Banner)
└── Page Components
    └── Feature Components
```

### 3. **Separation of Concerns**
- **Pages**: High-level page components that compose features
- **Components**: Reusable UI components (layout, common)
- **Services**: API calls and business logic
- **Hooks**: Custom React hooks for data fetching
- **Constants**: Static configuration and data

### 4. **Import Patterns**

Clean imports using index files:
```javascript
// Before
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

// After
import { LoadingSpinner, ErrorMessage } from '../components/common';
```

### 5. **File Naming Conventions**
- **Components**: PascalCase (e.g., `ConnectorCard.jsx`)
- **Hooks**: camelCase with `use` prefix (e.g., `useConnectors.js`)
- **Services**: camelCase (e.g., `api.js`)
- **Constants**: camelCase (e.g., `navigation.js`)

## Component Responsibilities

### Layout Components
- **Sidebar**: Navigation menu with collapsible functionality
- **Header**: Top navigation bar with user info
- **Banner**: Promotional/notification banner

### Page Components
- **Dashboard**: Overview statistics and charts
- **Connectors**: Browse and configure data connectors
- **Servers**: Manage MCP server instances
- **ServerTools**: View and execute server tools

### Common Components
- **LoadingSpinner**: Consistent loading state
- **ErrorMessage**: Standardized error display

## Custom Hooks

### `useConnectors(shouldFetch)`
Fetches and manages connector data.
```javascript
const { connectors, loading, error } = useConnectors(true);
```

### `useServers(shouldFetch)`
Fetches and manages server data with refresh capability.
```javascript
const { servers, loading, error, refetch } = useServers(true);
```

### `useServerTools(serverId, shouldFetch)`
Fetches tools for a specific server.
```javascript
const { tools, loading, error } = useServerTools(serverId, true);
```

## API Service

Centralized API calls in `services/api.js`:
```javascript
import { api } from './services/api';

// Usage
const connectors = await api.getConnectors();
const servers = await api.getServers();
await api.createServer(serverData);
```

## Benefits of This Structure

1. **Better Code Organization**: Related files are grouped together
2. **Easier Navigation**: Clear directory structure
3. **Improved Maintainability**: Changes are isolated to specific features
4. **Reusability**: Common components can be easily reused
5. **Scalability**: Easy to add new pages and features
6. **Testing**: Each component can be tested independently
7. **Team Collaboration**: Clear boundaries between features

## Development Workflow

### Adding a New Page
1. Create directory: `src/pages/NewPage/`
2. Create main component: `NewPage.jsx`
3. Create `components/` subdirectory for page-specific components
4. Export from `index.js`
5. Add to `pages/index.js`
6. Update App.js routing

### Adding a New Component
1. Place in appropriate directory (`common/`, `layout/`, or page-specific)
2. Follow naming conventions
3. Export from index.js
4. Import and use

### Adding a New API Call
1. Add method to `services/api.js`
2. Create/update custom hook if needed
3. Use in component

## Migration Notes

The refactoring involved:
- Converting a 1,566-line monolithic `App.js` to a clean 77-line file
- Extracting 20+ components
- Creating 3 custom hooks
- Establishing clear patterns for future development
- Zero breaking changes - all functionality preserved

## Next Steps

Consider adding:
- Unit tests for components
- Storybook for component documentation
- PropTypes or TypeScript for type safety
- Context API for global state management
- Error boundaries for better error handling

