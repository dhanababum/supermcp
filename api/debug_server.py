"""
Debug script to test server creation
"""
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models import McpServer, McpServerToken
from api.database import get_session
import secrets

def test_server_creation():
    """Test creating a server and token"""
    try:
        with get_session() as session:
            print("✅ Database connection successful")
            
            # Test creating a server
            server_data = {
                "server_id": "test_debug",
                "server_name": "Test Debug Server",
                "configuration": {"test": "value"}
            }
            
            print(f"Creating server with data: {server_data}")
            mcp_server = McpServer(**server_data)
            session.add(mcp_server)
            session.commit()
            session.refresh(mcp_server)
            print(f"✅ Server created with ID: {mcp_server.id}")
            
            # Test creating a token
            token_value = f"mcp_token_{secrets.token_urlsafe(32)}"
            token = McpServerToken(
                token=token_value,
                mcp_server_id=mcp_server.id
            )
            session.add(token)
            session.commit()
            session.refresh(token)
            print(f"✅ Token created with ID: {token.id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing server creation...")
    success = test_server_creation()
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
