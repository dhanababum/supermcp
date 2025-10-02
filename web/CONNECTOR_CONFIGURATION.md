# Connector Configuration - Dynamic Form Feature

## Overview

The dynamic connector configuration feature allows users to configure connectors through a beautiful modal with forms that are automatically generated from JSON schemas. This uses **react-jsonschema-form (RJSF)** to create dynamic, validated forms.

## ✨ Features Implemented

### 1. **Dynamic Form Generation**
   - Forms are automatically generated from connector JSON schemas
   - Fetches schema from `/api/connector-schema/{connector_name}`
   - Supports all JSON Schema types (string, number, integer, enum, etc.)
   - Field validation based on schema requirements

### 2. **Beautiful Modal UI**
   - Gradient header (purple to blue)
   - Clean, modern design matching the dashboard
   - Responsive layout
   - Loading states with spinner
   - Error handling

### 3. **Form Features**
   - All standard input types supported
   - Dropdown selects for enums
   - Password fields with proper masking
   - Required field validation
   - Custom styling with Tailwind CSS
   - Real-time form state management

### 4. **User Experience**
   - Click "Configure" button on any connector card
   - Modal opens with loading state
   - Form appears with all fields from schema
   - Fill in configuration values
   - Save or Cancel
   - Form data logged to console (ready for backend integration)

## 🚀 How to Use

### Step 1: Navigate to Connectors
1. Go to `http://localhost:3000`
2. Click on "Connectors" in the sidebar

### Step 2: Configure a Connector
1. Find the connector you want to configure (e.g., "SQL databases")
2. Click the **"Configure"** button on the connector card
3. The configuration modal will open

### Step 3: Fill Out the Form
The form will display fields based on the connector's schema. For SQL databases, you'll see:

- **Connection Type** (dropdown): sqlite, postgres, mysql, mssql, oracle, snowflake
- **Username** (text): Database username
- **Password** (password): Database password (hidden input)
- **Host** (text): Database host address
- **Port** (number): Database port number
- **Database** (text): Database name

### Step 4: Save Configuration
1. Fill in all required fields (marked with *)
2. Click **"Save Configuration"**
3. Your configuration data will be logged and displayed in an alert
4. Modal closes automatically

## 📋 Example Schema

The system works with any JSON Schema. Here's the SQL database example:

```json
{
  "$defs": {
    "ConnectionType": {
      "enum": ["sqlite", "postgres", "mysql", "mssql", "oracle", "snowflake"],
      "title": "ConnectionType",
      "type": "string"
    }
  },
  "properties": {
    "connection_type": {
      "$ref": "#/$defs/ConnectionType"
    },
    "username": {
      "description": "The username for the database connection",
      "title": "Username",
      "type": "string"
    },
    "password": {
      "description": "The password for the database connection",
      "format": "password",
      "title": "Password",
      "type": "string",
      "writeOnly": true
    },
    "host": {
      "description": "The host for the database connection",
      "title": "Host",
      "type": "string"
    },
    "port": {
      "description": "The port for the database connection",
      "title": "Port",
      "type": "integer"
    },
    "database": {
      "description": "The database for the database connection",
      "title": "Database",
      "type": "string"
    }
  },
  "required": ["connection_type", "username", "password", "host", "port", "database"],
  "title": "SqlDbSchema",
  "type": "object"
}
```

## 🛠️ Technical Implementation

### Dependencies
```json
{
  "@rjsf/core": "^5.x.x",
  "@rjsf/utils": "^5.x.x",
  "@rjsf/validator-ajv8": "^5.x.x"
}
```

### Key Components

#### 1. State Management
```javascript
const [showConfigModal, setShowConfigModal] = useState(false);
const [selectedConnector, setSelectedConnector] = useState(null);
const [connectorSchema, setConnectorSchema] = useState(null);
const [loadingSchema, setLoadingSchema] = useState(false);
const [formData, setFormData] = useState({});
```

#### 2. Schema Fetching
```javascript
const handleConfigureConnector = (connector) => {
  setSelectedConnector(connector);
  setShowConfigModal(true);
  setLoadingSchema(true);
  
  fetch(`http://localhost:9000/api/connector-schema/${connector.id}`)
    .then(response => response.json())
    .then(schema => {
      setConnectorSchema(schema);
      setLoadingSchema(false);
    });
};
```

#### 3. Form Rendering
```javascript
<Form
  schema={connectorSchema}
  validator={validator}
  formData={formData}
  onChange={(e) => setFormData(e.formData)}
  onSubmit={handleFormSubmit}
/>
```

### API Endpoints Used

1. **GET `/api/connectors`**
   - Returns list of all available connectors

2. **GET `/api/connector-schema/{connector_name}`**
   - Returns JSON Schema for specific connector
   - Example: `/api/connector-schema/sql_db`

## 🎨 UI Customization

### Modal Styling
- **Header**: Gradient background (purple-600 to blue-600)
- **Body**: White background with max height and scroll
- **Footer**: Light gray background with action buttons
- **Overlay**: Semi-transparent gray backdrop

### Form Styling
All form elements are styled with Tailwind CSS:
- Rounded corners (0.5rem)
- Purple focus rings
- Proper spacing and padding
- Error messages in red
- Required field indicators

### Custom CSS Classes
Located in `src/index.css`:
- `.rjsf-form-wrapper` - Main form container
- Form inputs styled with consistent colors
- Focus states with purple accent
- Error messages in red

## 🔄 Data Flow

```
User clicks "Configure"
  → handleConfigureConnector() called
    → Modal opens with loading state
      → Fetch schema from API
        → Schema loads into form
          → User fills form
            → User clicks "Save Configuration"
              → handleFormSubmit() called
                → Form data processed
                  → Modal closes
```

## 📦 Backend Integration (Next Steps)

Currently, the form data is just displayed in an alert. To fully integrate:

### 1. Create Save Endpoint
Add to `api/main.py`:
```python
@router.post("/connector-config/{connector_name}")
def save_connector_config(connector_name: str, config: dict):
    # Save configuration to database
    # Return success response
    return {"status": "success", "connector": connector_name}
```

### 2. Update handleFormSubmit
```javascript
const handleFormSubmit = ({ formData }) => {
  fetch(`http://localhost:9000/api/connector-config/${selectedConnector.id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  })
  .then(response => response.json())
  .then(data => {
    alert('Configuration saved successfully!');
    setShowConfigModal(false);
  });
};
```

## 🔮 Advanced Features (Future)

### 1. Conditional Fields
Use JSON Schema `if/then/else` for dynamic fields:
```json
{
  "if": {
    "properties": { "connection_type": { "const": "postgres" } }
  },
  "then": {
    "properties": {
      "ssl_mode": { "type": "string", "enum": ["require", "prefer", "disable"] }
    }
  }
}
```

### 2. Custom Widgets
Add custom input components:
```javascript
const customWidgets = {
  ColorPicker: ColorPickerWidget,
  FileUpload: FileUploadWidget
};

<Form
  schema={schema}
  widgets={customWidgets}
  validator={validator}
/>
```

### 3. Field Dependencies
Use `dependencies` keyword for field relationships:
```json
{
  "dependencies": {
    "use_ssl": {
      "properties": {
        "ssl_cert": { "type": "string" }
      }
    }
  }
}
```

### 4. Validation Messages
Custom error messages:
```javascript
const customFormats = {
  ipAddress: /^(\d{1,3}\.){3}\d{1,3}$/
};

const transformErrors = (errors) => {
  return errors.map(error => {
    if (error.name === "pattern") {
      error.message = "Please enter a valid IP address";
    }
    return error;
  });
};
```

## 🐛 Troubleshooting

### Modal Doesn't Open
- Check browser console for errors
- Verify API endpoint is accessible
- Ensure connector has a valid ID

### Form Not Displaying
- Verify schema is valid JSON Schema
- Check network tab for API response
- Look for validation errors in console

### Styling Issues
- Ensure Tailwind CSS is properly configured
- Check that custom CSS is loaded
- Verify class names in modal component

### Submission Not Working
- Open browser console to see form data
- Check that form validation passes
- Verify all required fields are filled

## 📚 Resources

- [react-jsonschema-form Documentation](https://rjsf-team.github.io/react-jsonschema-form/)
- [JSON Schema Specification](https://json-schema.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)

## ✅ Testing Checklist

- [ ] Click Configure button opens modal
- [ ] Modal displays loading state
- [ ] Form fields render from schema
- [ ] Required fields are marked
- [ ] Dropdown shows enum values
- [ ] Password field masks input
- [ ] Form validation works
- [ ] Save button triggers submission
- [ ] Cancel button closes modal
- [ ] Click outside modal closes it
- [ ] Form data is logged correctly

Enjoy your dynamic connector configuration forms! 🎉

