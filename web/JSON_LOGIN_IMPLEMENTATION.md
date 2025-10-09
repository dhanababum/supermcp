# JSON Login Implementation

## ✅ **Implemented: JSON-Based Authentication**

Your application now supports **JSON-based login** instead of form-encoded data!

## 🎯 **What Changed**

### Backend: New Custom JSON Login Endpoint

Added `/auth/json-login` endpoint that:
- ✅ Accepts JSON payload (`application/json`)
- ✅ Uses `email` field (not `username`)
- ✅ Returns cookie authentication (same as standard login)
- ✅ Returns user information in response
- ✅ Compatible with `fastapi-users` ecosystem

**Endpoint:** `POST /auth/json-login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response (Success):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "is_active": true,
    "is_superuser": false,
    "is_verified": false
  }
}
```

**Response (Error):**
```json
{
  "detail": "LOGIN_BAD_CREDENTIALS"
}
```

### Frontend: Updated to Send JSON

**Before (Form Data):**
```javascript
const form = new FormData();
form.append('username', email);
form.append('password', password);

fetch('/auth/cookie/login', {
  method: 'POST',
  body: form
});
```

**After (JSON):**
```javascript
const payload = {
  email: formData.email,
  password: formData.password
};

fetch('/auth/json-login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
  body: JSON.stringify(payload)
});
```

## 📋 **API Endpoints Available**

### 1. **JSON Login** (New - Recommended)
```bash
curl -X POST http://localhost:9000/auth/json-login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }' \
  --cookie-jar cookies.txt
```

### 2. **Form-Based Login** (Original - Still Available)
```bash
curl -X POST http://localhost:9000/auth/cookie/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123" \
  --cookie-jar cookies.txt
```

### 3. **JWT Login** (Also Available)
```bash
curl -X POST http://localhost:9000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

## 🔧 **Implementation Details**

### Backend Code (`api/main.py`)

```python
from pydantic import BaseModel

class JSONLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/json-login")
async def json_login(
    credentials: JSONLoginRequest,
    response: Response,
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    Custom login endpoint that accepts JSON payload.
    Returns a cookie for authentication.
    """
    try:
        # Authenticate user
        user = await user_manager.authenticate(
            credentials.email,
            credentials.password
        )

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="LOGIN_BAD_CREDENTIALS"
            )

        # Get the cookie strategy and create token
        from users import cookie_auth_backend
        strategy = cookie_auth_backend.get_strategy()
        token = await strategy.write_token(user)

        # Set the cookie in response
        from users import cookie_transport
        await cookie_transport.get_login_response(token, response)

        return {
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "is_verified": user.is_verified
            }
        }

    except (UserNotExists, InvalidPasswordException):
        raise HTTPException(
            status_code=400,
            detail="LOGIN_BAD_CREDENTIALS"
        )
```

### Frontend Code (`web/src/pages/Auth/Auth.jsx`)

```javascript
const handleLogin = async (formData) => {
  setLoading(true);
  setError(null);
  setFieldErrors({});

  try {
    // Send JSON payload
    const payload = {
      email: formData.email,
      password: formData.password
    };

    const response = await fetch('http://localhost:9000/auth/json-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      const data = await response.json();
      console.log('Login successful:', data);
      navigate('/dashboard');
    } else {
      // Handle errors...
    }
  } catch (error) {
    setError('Network error. Please try again.');
  } finally {
    setLoading(false);
  }
};
```

## 🚀 **Benefits**

### 1. **Modern API Design**
- ✅ Uses JSON (standard for modern APIs)
- ✅ Consistent with other endpoints
- ✅ Easier to work with in JavaScript

### 2. **Better Developer Experience**
- ✅ No need to convert to FormData
- ✅ Direct object serialization
- ✅ Type-safe with TypeScript

### 3. **Maintains Security**
- ✅ Still uses cookie authentication
- ✅ Same security model as form login
- ✅ HttpOnly cookies prevent XSS
- ✅ SameSite protection against CSRF

### 4. **Backward Compatible**
- ✅ Original form endpoint still works
- ✅ Can switch between endpoints easily
- ✅ No breaking changes for existing clients

## 🧪 **Testing**

### Test with curl:
```bash
# 1. Create a user (if not exists)
curl -X POST http://localhost:9000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "is_active": true,
    "is_superuser": false,
    "is_verified": false
  }'

# 2. Login with JSON
curl -X POST http://localhost:9000/auth/json-login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }' \
  --cookie-jar cookies.txt \
  -v

# 3. Test authenticated route
curl -X GET http://localhost:9000/authenticated-route \
  --cookie cookies.txt
```

### Test in Browser:
1. Start backend: `cd api && uv run uvicorn main:app --reload --port 9000`
2. Start frontend: `cd web && npm start`
3. Navigate to `http://localhost:3000/auth/login`
4. Enter credentials and submit
5. Check browser console for logs
6. Should redirect to dashboard on success

## 📊 **Request/Response Examples**

### Successful Login
**Request:**
```http
POST /auth/json-login HTTP/1.1
Host: localhost:9000
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "testpassword123"
}
```

**Response:**
```http
HTTP/1.1 200 OK
Set-Cookie: auth_cookie=eyJ...; Path=/; HttpOnly; SameSite=lax
Content-Type: application/json

{
  "message": "Login successful",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "is_active": true,
    "is_superuser": false,
    "is_verified": false
  }
}
```

### Failed Login (Bad Credentials)
**Request:**
```http
POST /auth/json-login HTTP/1.1
Host: localhost:9000
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "wrongpassword"
}
```

**Response:**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "detail": "LOGIN_BAD_CREDENTIALS"
}
```

### Failed Login (Missing Fields)
**Request:**
```http
POST /auth/json-login HTTP/1.1
Host: localhost:9000
Content-Type: application/json

{
  "email": "test@example.com"
}
```

**Response:**
```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "password"],
      "msg": "Field required",
      "input": {"email": "test@example.com"}
    }
  ]
}
```

## 🔐 **Security Considerations**

### ✅ **What We Did Right:**

1. **HttpOnly Cookies**: Prevents JavaScript access (XSS protection)
2. **SameSite=lax**: Prevents CSRF attacks
3. **CORS with credentials**: Only allows localhost:3000
4. **Secure password hashing**: Uses `fastapi-users` built-in hashing
5. **Active user check**: Only allows active users to login

### ⚠️ **Production Considerations:**

1. **HTTPS Required**: Set `cookie_secure=True` in production
2. **Update CORS origins**: Change from localhost to production domain
3. **Rate limiting**: Add rate limiting to prevent brute force
4. **Password requirements**: Enforce strong passwords
5. **Account lockout**: Implement after X failed attempts

## 🎉 **Summary**

Your application now has:

✅ **JSON-based login** - Modern API design  
✅ **Cookie authentication** - Secure and stateless  
✅ **Field validation** - Client and server-side  
✅ **Error handling** - Comprehensive and user-friendly  
✅ **Debug logging** - Easy troubleshooting  
✅ **Backward compatible** - Original endpoints still work  

**The login now sends `application/json` payloads as requested!** 🚀
