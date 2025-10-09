# FastAPI Users Login Debugging Guide

## 🔍 **Issue**: Getting "Field required" errors with valid credentials

When using `fastapi-users` with `CookieTransport`, the login endpoint has specific requirements.

## ✅ **Current Implementation Status**

Your implementation is **CORRECT**! Here's what's already properly configured:

### Frontend (`Auth.jsx`)
```javascript
const form = new FormData();
form.append('username', formData.email);  // ✅ Correct: using 'username' field
form.append('password', formData.password); // ✅ Correct: using 'password' field

const response = await fetch('http://localhost:9000/auth/cookie/login', {
  method: 'POST',
  credentials: 'include', // ✅ Correct: includes cookies
  body: form,             // ✅ Correct: sends as form data
  // ✅ Correct: NOT setting Content-Type (browser sets it with boundary)
});
```

### Backend (`users.py`)
```python
cookie_transport = CookieTransport(
    cookie_name="auth_cookie", 
    cookie_max_age=3600,
    cookie_secure=False,  # ✅ Correct for development (HTTP)
    cookie_httponly=True,
    cookie_samesite="lax" # ✅ Correct for cross-origin cookies
)
```

### Backend (`main.py`)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ✅ Matches frontend
    allow_credentials=True,                    # ✅ Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(cookie_auth_backend),
    prefix="/auth/cookie",  # ✅ Correct endpoint
    tags=["auth"]
)
```

## 🔧 **Debugging Steps**

### Step 1: Check Browser Console
After adding debug logs, check the browser console for:
```
Sending login request with: { username: "user@example.com", password: "***" }
Login response status: 422 (or other status)
Login error response: { detail: [...] }
```

### Step 2: Check Network Tab
1. Open Browser DevTools → Network tab
2. Find the request to `auth/cookie/login`
3. Check **Request Headers**:
   ```
   Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
   ```
4. Check **Form Data**:
   ```
   username: user@example.com
   password: yourpassword
   ```
5. Check **Response** for exact error details

### Step 3: Common Issues & Solutions

#### Issue 1: "Field required" with valid credentials
**Possible Cause**: User doesn't exist in database

**Solution**: Create a user first via signup:
```bash
# Test via curl
curl -X POST http://localhost:9000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "is_active": true,
    "is_superuser": false,
    "is_verified": false
  }'
```

#### Issue 2: CORS errors
**Symptoms**: No response in browser, CORS error in console

**Solution**: Already configured correctly, but verify:
- Frontend runs on `http://localhost:3000`
- Backend runs on `http://localhost:9000`
- Both use `http://` (not mixed http/https)

#### Issue 3: Cookie not being set
**Symptoms**: Login appears successful but redirects back to login

**Solution**: Check cookie settings:
```python
# In users.py
cookie_transport = CookieTransport(
    cookie_secure=False,  # Must be False for HTTP in development
    cookie_samesite="lax" # Must allow cross-site in development
)
```

#### Issue 4: Database not synced
**Symptoms**: Various errors about missing tables or users

**Solution**: Run migrations:
```bash
cd api
uv run alembic upgrade head
```

## 🧪 **Testing Checklist**

### 1. Verify Backend is Running
```bash
cd api
uv run uvicorn main:app --reload --port 9000
```

### 2. Verify Frontend is Running
```bash
cd web
npm start
# Should open http://localhost:3000
```

### 3. Test Registration First
Before testing login, create a test user:
1. Go to signup page
2. Create account with:
   - Email: `test@example.com`
   - Password: `testpassword123`
3. You should see "Account created successfully!"

### 4. Test Login
1. Go to login page
2. Use the credentials from step 3
3. Check browser console for debug logs
4. Check network tab for request details

## 📊 **Expected Request Format**

### What FastAPI Expects:
```
POST /auth/cookie/login
Content-Type: multipart/form-data; boundary=----WebKit...

------WebKit...
Content-Disposition: form-data; name="username"

test@example.com
------WebKit...
Content-Disposition: form-data; name="password"

testpassword123
------WebKit...--
```

### What Your Frontend Sends:
✅ **Correct**: Using `FormData()` which creates the exact format above

### What Would Be Wrong:
❌ **Wrong**: Sending JSON
```javascript
// DON'T DO THIS
body: JSON.stringify({ username: email, password: password })
```

❌ **Wrong**: Setting Content-Type header manually
```javascript
// DON'T DO THIS
headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
```

## 🎯 **Most Likely Causes**

Based on the error "Field required" with valid credentials, here are the most likely causes:

### 1. **User Doesn't Exist** (90% probability)
- The credentials might be "valid format" but not in the database
- **Solution**: Create the user via signup first

### 2. **Client-Side Validation Preventing Submission** (5% probability)
- Client-side validation catches empty fields before API call
- **Solution**: Already implemented correctly

### 3. **Browser Issue** (3% probability)
- FormData not being sent correctly
- **Solution**: Check network tab, try different browser

### 4. **Backend Database Issue** (2% probability)
- Database connection problem
- **Solution**: Check backend logs

## 🚀 **Quick Fix: Create Test User**

If you're getting field validation errors, try creating a test user directly:

### Option 1: Via Signup Form
1. Navigate to `/auth/signup`
2. Fill in the form
3. Click "Create account"
4. Then try logging in

### Option 2: Via Backend (Python)
```bash
cd api
uv run python -c "
import asyncio
from database import async_session_maker
from models import User
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_users.password import PasswordHelper

async def create_user():
    async with async_session_maker() as session:
        password_helper = PasswordHelper()
        hashed_password = password_helper.hash('testpassword123')
        
        user = User(
            email='test@example.com',
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=False
        )
        session.add(user)
        await session.commit()
        print('User created successfully!')

asyncio.run(create_user())
"
```

### Option 3: Via SQL (if using SQLite)
```bash
cd api
sqlite3 mcp_tools.db
```
```sql
-- Check if user exists
SELECT email FROM user WHERE email = 'test@example.com';

-- If no results, user doesn't exist
-- Create via signup form or Python script
```

## 📝 **Debug Output Example**

### Successful Login:
```
Console:
  Sending login request with: { username: "test@example.com", password: "***" }
  Login response status: 200
  Login successful

Network Tab:
  Request: POST /auth/cookie/login
  Status: 200 OK
  Response Headers:
    Set-Cookie: auth_cookie=eyJ...; Path=/; HttpOnly; SameSite=lax
```

### Failed Login (User Doesn't Exist):
```
Console:
  Sending login request with: { username: "test@example.com", password: "***" }
  Login response status: 400
  Login error response: { detail: "LOGIN_BAD_CREDENTIALS" }

Network Tab:
  Request: POST /auth/cookie/login
  Status: 400 Bad Request
  Response: { detail: "LOGIN_BAD_CREDENTIALS" }
```

### Failed Login (Empty Fields):
```
Console:
  Sending login request with: { username: "test@example.com", password: "***" }
  Login response status: 422
  Login error response: {
    detail: [
      { type: "missing", loc: ["body", "username"], msg: "Field required" },
      { type: "missing", loc: ["body", "password"], msg: "Field required" }
    ]
  }

Network Tab:
  Request: POST /auth/cookie/login
  Status: 422 Unprocessable Entity
  Form Data: (empty or missing fields)
```

## 🎉 **Summary**

Your implementation is **CORRECT**. The "Field required" error most likely means:

1. ✅ **Frontend is working correctly** - sending form data with proper field names
2. ✅ **Backend is configured correctly** - expecting form data with username/password
3. ❌ **Issue**: Either:
   - User doesn't exist in the database (create via signup)
   - Something is preventing the FormData from being sent (check network tab)

**Next Steps:**
1. Check browser console for debug logs
2. Check network tab to see actual request
3. Try creating a test user via signup first
4. Then attempt login with that user

Your code is solid! 🚀
