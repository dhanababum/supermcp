# 🚀 Quick Start: Test the Dynamic Configuration Form

## ✅ What's Ready

Both servers are running:
- ✅ **React Frontend**: http://localhost:3000
- ✅ **FastAPI Backend**: http://localhost:9000

## 🎯 Test in 3 Simple Steps

### Step 1: Open the Dashboard
Open your browser to: **http://localhost:3000**

### Step 2: Go to Connectors
Click on **"Connectors"** in the sidebar (3rd menu item)

### Step 3: Configure SQL Connector
1. You'll see the **"SQL databases"** connector card
2. Click the **"Configure"** button
3. A beautiful modal will appear! ✨

## 📝 What You'll See

The configuration modal will display a form with these fields:

| Field | Type | Description |
|-------|------|-------------|
| **Connection Type** | Dropdown | Choose from: sqlite, postgres, mysql, mssql, oracle, snowflake |
| **Username** | Text | Database username |
| **Password** | Password | Database password (masked) |
| **Host** | Text | Database host address |
| **Port** | Number | Database port number |
| **Database** | Text | Database name |

All fields are **required** and validated!

## 🎨 Modal Features

- **Beautiful gradient header** (purple to blue)
- **Loading spinner** while fetching schema
- **Auto-generated form** from JSON schema
- **Real-time validation**
- **Purple focus states** on inputs
- **Error messages** for invalid fields
- **Cancel** or **Save** buttons

## 🧪 Try It Out

### Example Configuration:
```
Connection Type: postgres
Username: admin
Password: secret123
Host: localhost
Port: 5432
Database: myapp_db
```

Click **"Save Configuration"** and you'll see an alert with your configuration data!

## 🔍 What Happens Behind the Scenes

1. **Click Configure** → `handleConfigureConnector()` fires
2. **Fetch Schema** → GET `/api/connector-schema/sql_db`
3. **Render Form** → react-jsonschema-form generates fields
4. **Fill Form** → User enters data
5. **Submit** → `handleFormSubmit()` processes data
6. **Alert** → Shows configuration (ready for backend save)

## 🎥 Expected Behavior

### When Modal Opens:
- ⏳ Shows loading spinner
- 🔄 Fetches schema from API
- ✅ Displays form with all fields

### When Filling Form:
- 🎯 Focus states highlight in purple
- ✅ Validation happens in real-time
- 📝 Field descriptions show below inputs

### When Submitting:
- 🚀 Form data is collected
- 📋 Alert shows configuration
- ❌ Modal closes

## 🛠️ Backend API Test

You can also test the API directly:

### Get Connectors:
```bash
curl http://localhost:9000/api/connectors
```

### Get SQL Schema:
```bash
curl http://localhost:9000/api/connector-schema/sql_db
```

Should return:
```json
{
  "properties": {
    "connection_type": { ... },
    "username": { "type": "string", ... },
    "password": { "type": "string", "format": "password", ... },
    "host": { "type": "string", ... },
    "port": { "type": "integer", ... },
    "database": { "type": "string", ... }
  },
  "required": ["connection_type", "username", "password", "host", "port", "database"]
}
```

## 🎓 Learning Points

This implementation demonstrates:
- ✅ **Dynamic form generation** from JSON schemas
- ✅ **Modal UI patterns** with React
- ✅ **State management** with hooks
- ✅ **API integration** (fetch)
- ✅ **Form validation** with JSON Schema
- ✅ **Tailwind CSS** styling
- ✅ **react-jsonschema-form** library usage

## 📸 Screenshots Description

You should see:

1. **Connectors Grid**
   - SQL databases card with gradient icon
   - Configure button in purple

2. **Configuration Modal**
   - Gradient header "Configure SQL databases"
   - Form with 6 input fields
   - Cancel and Save buttons at bottom

3. **Form Fields**
   - Connection Type dropdown
   - Text inputs for username, host, database
   - Password input (masked)
   - Number input for port

## 🔧 Next Steps

To fully integrate with backend:

1. Create a POST endpoint to save configuration
2. Store config in database
3. Add validation error handling
4. Show success/error notifications
5. Refresh connector status after save

See `CONNECTOR_CONFIGURATION.md` for detailed backend integration guide!

## 🐛 Troubleshooting

### Modal doesn't open?
- Check browser console (F12)
- Verify both servers are running

### Form doesn't show?
- Check Network tab for API call
- Verify schema endpoint returns data

### Can't submit?
- Fill all required fields
- Check console for validation errors

---

**Ready to test?** Go to http://localhost:3000 and click Connectors! 🎉

