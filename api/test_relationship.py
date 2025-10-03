"""
Test script for McpServer and McpServerToken relationship.
Run with: uv run python test_relationship.py
"""
from sqlmodel import Session, select
from models import McpServer, McpServerToken
from database import engine


def test_create_server_with_tokens():
    """Test creating a server and adding tokens to it."""
    print("\n🧪 Test 1: Creating server with tokens...")
    
    with Session(engine) as session:
        # Create server
        server = McpServer(
            name="Production Server",
            url="https://mcp.prod.example.com",
            description="Main production MCP server instance"
        )
        session.add(server)
        session.commit()
        session.refresh(server)
        
        print(f"✅ Created server: {server.name} (ID: {server.id})")
        
        # Create multiple tokens for this server
        tokens_data = [
            "prod_token_abc123",
            "prod_token_def456", 
            "prod_token_ghi789"
        ]
        
        for token_str in tokens_data:
            token = McpServerToken(
                token=token_str,
                mcp_server_id=server.id
            )
            session.add(token)
        
        session.commit()
        session.refresh(server)
        
        print(f"✅ Created {len(server.tokens)} tokens for server")
        
        # Verify relationship works
        for token in server.tokens:
            assert token.server.id == server.id
            assert token.server.name == server.name
            print(f"   - Token: {token.token}")
        
        print("✅ Test 1 passed!\n")
        return server.id


def test_access_server_from_token(server_id):
    """Test accessing server from a token (many-to-one)."""
    print("🧪 Test 2: Accessing server from token...")
    
    with Session(engine) as session:
        # Get a token
        statement = select(McpServerToken).where(
            McpServerToken.mcp_server_id == server_id
        ).limit(1)
        token = session.exec(statement).first()
        
        if token:
            print(f"✅ Found token: {token.token}")
            
            # Access server through relationship
            if token.server:
                print(f"✅ Token belongs to server: {token.server.name}")
                print(f"   Server URL: {token.server.url}")
                assert token.server.id == server_id
            else:
                print("❌ Token has no associated server!")
                return False
        
        print("✅ Test 2 passed!\n")
        return True


def test_query_all_servers_with_tokens():
    """Test querying all servers and their tokens."""
    print("🧪 Test 3: Querying all servers with token counts...")
    
    with Session(engine) as session:
        servers = session.exec(select(McpServer)).all()
        
        print(f"✅ Found {len(servers)} server(s):")
        for server in servers:
            print(f"   - {server.name}: {len(server.tokens)} token(s)")
            for token in server.tokens:
                print(f"     • {token.token[:20]}...")
        
        print("✅ Test 3 passed!\n")


def test_create_using_relationship():
    """Test creating server and tokens using relationship."""
    print("🧪 Test 4: Creating server and tokens via relationship...")
    
    with Session(engine) as session:
        # Create server with tokens using relationship
        server = McpServer(
            name="Development Server",
            url="https://mcp.dev.example.com",
            description="Development environment MCP server"
        )
        
        # Add tokens through relationship
        server.tokens = [
            McpServerToken(token="dev_token_001"),
            McpServerToken(token="dev_token_002")
        ]
        
        session.add(server)
        session.commit()
        session.refresh(server)
        
        print(f"✅ Created server: {server.name}")
        print(f"✅ With {len(server.tokens)} tokens via relationship")
        
        # Verify all tokens have correct server_id
        for token in server.tokens:
            assert token.mcp_server_id == server.id
            assert token.server.id == server.id
            print(f"   - {token.token}")
        
        print("✅ Test 4 passed!\n")


def cleanup_test_data():
    """Clean up test data."""
    print("🧹 Cleaning up test data...")
    
    with Session(engine) as session:
        # Delete all test tokens
        tokens = session.exec(select(McpServerToken)).all()
        for token in tokens:
            session.delete(token)
        
        # Delete all test servers
        servers = session.exec(select(McpServer)).all()
        for server in servers:
            session.delete(server)
        
        session.commit()
        print("✅ Cleanup complete!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing McpServer ↔ McpServerToken Relationship")
    print("=" * 60)
    
    try:
        # Run tests
        server_id = test_create_server_with_tokens()
        test_access_server_from_token(server_id)
        test_query_all_servers_with_tokens()
        test_create_using_relationship()
        
        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        # Ask if user wants to cleanup
        response = input("\nClean up test data? (y/n): ").lower()
        if response == 'y':
            cleanup_test_data()
        else:
            print("Test data kept in database.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

