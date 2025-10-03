# McpServer and McpServerToken Relationship

## ✅ Relationship Implemented

The many-to-one relationship between `McpServerToken` (many) and `McpServer` (one) has been successfully implemented!

## 📊 Database Schema

### McpServer Table (Parent)
```sql
CREATE TABLE mcp_servers (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    url VARCHAR,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX ix_mcp_servers_name ON mcp_servers(name);
```

### McpServerToken Table (Child)
```sql
CREATE TABLE mcp_server_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR NOT NULL,
    mcp_server_id INTEGER,  -- Foreign Key to mcp_servers.id
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(id)
);
```

## 🔗 Relationship Type

**Many-to-One**: Multiple tokens can belong to one server

```
McpServerToken (many) ──────► McpServer (one)
                  mcp_server_id

One McpServer can have many McpServerTokens
```

## 💻 Usage Examples

### 1. Create a Server with Tokens

```python
from sqlmodel import Session, select
from api.models import McpServer, McpServerToken
from api.database import engine

with Session(engine) as session:
    # Create a server
    server = McpServer(
        name="Production Server",
        url="https://mcp.example.com",
        description="Main production MCP server"
    )
    session.add(server)
    session.commit()
    session.refresh(server)
    
    # Create tokens for this server
    token1 = McpServerToken(
        token="token_abc123",
        mcp_server_id=server.id
    )
    token2 = McpServerToken(
        token="token_def456",
        mcp_server_id=server.id
    )
    
    session.add(token1)
    session.add(token2)
    session.commit()
    
    print(f"Created server: {server.name}")
    print(f"With {len(server.tokens)} tokens")
```

### 2. Access Tokens from Server

```python
with Session(engine) as session:
    # Get server with all its tokens
    statement = select(McpServer).where(McpServer.name == "Production Server")
    server = session.exec(statement).first()
    
    # Access tokens through relationship
    for token in server.tokens:
        print(f"Token: {token.token}")
```

### 3. Access Server from Token

```python
with Session(engine) as session:
    # Get a token
    statement = select(McpServerToken).where(McpServerToken.token == "token_abc123")
    token = session.exec(statement).first()
    
    # Access server through relationship
    if token.server:
        print(f"Token belongs to server: {token.server.name}")
```

### 4. Query All Servers with Token Count

```python
with Session(engine) as session:
    servers = session.exec(select(McpServer)).all()
    
    for server in servers:
        print(f"{server.name}: {len(server.tokens)} tokens")
```

### 5. Create Server and Tokens Together

```python
with Session(engine) as session:
    server = McpServer(
        name="Development Server",
        url="https://dev.mcp.example.com"
    )
    
    # Add tokens before committing server
    server.tokens = [
        McpServerToken(token="dev_token_1"),
        McpServerToken(token="dev_token_2"),
        McpServerToken(token="dev_token_3")
    ]
    
    session.add(server)
    session.commit()
```

### 6. Filter Tokens by Server

```python
with Session(engine) as session:
    # Get server ID
    server = session.exec(
        select(McpServer).where(McpServer.name == "Production Server")
    ).first()
    
    # Get all active tokens for this server
    tokens = session.exec(
        select(McpServerToken)
        .where(McpServerToken.mcp_server_id == server.id)
        .where(McpServerToken.is_active == True)
    ).all()
    
    for token in tokens:
        print(f"Active token: {token.token}")
```

## 🔧 FastAPI Endpoint Examples

### Create Server with Tokens

```python
from fastapi import APIRouter, Depends
from sqlmodel import Session
from api.models import McpServer, McpServerToken
from api.database import get_session
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CreateServerRequest(BaseModel):
    name: str
    url: str | None = None
    description: str | None = None
    tokens: List[str] = []

@router.post("/mcp-servers")
def create_server(
    request: CreateServerRequest,
    session: Session = Depends(get_session)
):
    # Create server
    server = McpServer(
        name=request.name,
        url=request.url,
        description=request.description
    )
    session.add(server)
    session.commit()
    session.refresh(server)
    
    # Create tokens
    for token_str in request.tokens:
        token = McpServerToken(
            token=token_str,
            mcp_server_id=server.id
        )
        session.add(token)
    
    session.commit()
    session.refresh(server)
    
    return {
        "id": server.id,
        "name": server.name,
        "tokens_count": len(server.tokens)
    }
```

### Get Server with Tokens

```python
@router.get("/mcp-servers/{server_id}")
def get_server(
    server_id: int,
    session: Session = Depends(get_session)
):
    server = session.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    return {
        "id": server.id,
        "name": server.name,
        "url": server.url,
        "description": server.description,
        "tokens": [
            {
                "id": token.id,
                "token": token.token,
                "is_active": token.is_active
            }
            for token in server.tokens
        ]
    }
```

### Add Token to Existing Server

```python
class AddTokenRequest(BaseModel):
    token: str

@router.post("/mcp-servers/{server_id}/tokens")
def add_token_to_server(
    server_id: int,
    request: AddTokenRequest,
    session: Session = Depends(get_session)
):
    server = session.get(McpServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    token = McpServerToken(
        token=request.token,
        mcp_server_id=server.id
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    
    return {
        "token_id": token.id,
        "server_id": server.id,
        "server_name": server.name
    }
```

## 🎯 Relationship Features

### Bidirectional Access

**From Server to Tokens:**
```python
server.tokens  # Returns List[McpServerToken]
```

**From Token to Server:**
```python
token.server  # Returns Optional[McpServer]
```

### Automatic Updates

When you add tokens to a server's `tokens` list, SQLModel automatically sets the `mcp_server_id`:

```python
server = McpServer(name="Test")
server.tokens.append(McpServerToken(token="test123"))
# SQLModel automatically sets token.mcp_server_id = server.id
```

### Cascade Behavior

Currently using default cascade (no cascade delete). To enable cascade delete:

```python
class McpServer(SQLModel, table=True):
    tokens: List["McpServerToken"] = Relationship(
        back_populates="server",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

## ✅ Migration Applied

The migration `f1fb9ea4a9e2` has been applied successfully:

- ✅ Created `mcp_servers` table
- ✅ Created `mcp_server_tokens` table  
- ✅ Added foreign key constraint `mcp_server_id` → `mcp_servers.id`
- ✅ Created index on `mcp_servers.name`
- ✅ Established bidirectional relationship

## 🧪 Testing the Relationship

Create a test file `test_relationship.py`:

```python
from sqlmodel import Session, select
from api.models import McpServer, McpServerToken
from api.database import engine

def test_relationship():
    with Session(engine) as session:
        # Create server
        server = McpServer(
            name="Test Server",
            url="https://test.com"
        )
        session.add(server)
        session.commit()
        session.refresh(server)
        
        # Create tokens
        for i in range(3):
            token = McpServerToken(
                token=f"token_{i}",
                mcp_server_id=server.id
            )
            session.add(token)
        
        session.commit()
        session.refresh(server)
        
        # Test relationship
        print(f"Server: {server.name}")
        print(f"Tokens: {len(server.tokens)}")
        
        for token in server.tokens:
            print(f"  - {token.token} (belongs to {token.server.name})")
        
        # Verify
        assert len(server.tokens) == 3
        assert all(t.server.id == server.id for t in server.tokens)
        print("✅ Relationship test passed!")

if __name__ == "__main__":
    test_relationship()
```

Run it:
```bash
cd api
uv run python test_relationship.py
```

## 📚 SQLModel Relationship Documentation

For more details on SQLModel relationships:
- [SQLModel Relationships](https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/)
- [One-to-Many Relationships](https://sqlmodel.tiangolo.com/tutorial/relationship-attributes/one-to-many/)

## 🔍 Verify in Database

```sql
-- Check tables exist
\dt

-- Check mcp_servers structure
\d mcp_servers

-- Check mcp_server_tokens structure
\d mcp_server_tokens

-- View foreign key constraint
SELECT
    tc.table_name, 
    tc.constraint_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'mcp_server_tokens' 
  AND tc.constraint_type = 'FOREIGN KEY';
```

---

**Status**: ✅ **Relationship Successfully Implemented and Migrated!**

You can now use the many-to-one relationship between McpServerToken and McpServer in your application! 🚀

