#!/usr/bin/env python3
"""
Simple script to update McpServer records with server_url from their corresponding connector URLs.
Uses direct SQL updates to avoid SQLModel/SQLAlchemy row object issues.
"""

import sys
import os
from sqlalchemy import text
from sqlmodel import Session

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine


def update_server_urls():
    """
    Update all McpServer records with server_url from their corresponding connector URLs.
    """
    with Session(engine) as session:
        try:
            # First, let's see what we have
            print("Current servers and connectors:")
            
            # Get servers
            servers_result = session.exec(text("""
                SELECT id, connector_id, server_name, server_url 
                FROM mcp_servers 
                WHERE is_active = true
            """)).all()
            
            print(f"Found {len(servers_result)} active servers:")
            for server in servers_result:
                print(f"  Server ID: {server[0]}, Name: {server[2]}, Connector: {server[1]}, URL: {server[3]}")
            
            # Get connectors
            connectors_result = session.exec(text("""
                SELECT id, name, url 
                FROM mcp_connectors 
                WHERE is_active = true
            """)).all()
            
            print(f"\nFound {len(connectors_result)} active connectors:")
            for connector in connectors_result:
                print(f"  Connector ID: {connector[0]}, Name: {connector[1]}, URL: {connector[2]}")
            
            print("\nUpdating servers...")
            
            # Update servers with connector URLs
            update_result = session.exec(text("""
                UPDATE mcp_servers 
                SET server_url = c.url, updated_at = NOW()
                FROM mcp_connectors c
                WHERE mcp_servers.connector_id = c.id::text
                AND mcp_servers.is_active = true
                AND c.is_active = true
            """))
            
            session.commit()
            
            print(f"Updated {update_result.rowcount} servers")
            
            # Verify the updates
            print("\nVerification - Updated servers:")
            updated_servers = session.exec(text("""
                SELECT id, connector_id, server_name, server_url 
                FROM mcp_servers 
                WHERE is_active = true AND server_url IS NOT NULL
            """)).all()
            
            for server in updated_servers:
                print(f"  Server ID: {server[0]}, Name: {server[2]}, Connector: {server[1]}, URL: {server[3]}")
            
            return True
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            session.rollback()
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("MCP Server URL Update Script (Simple Version)")
    print("=" * 60)
    print("This script will update all McpServer records with server_url")
    print("from their corresponding McpConnector URLs using direct SQL.")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    print()
    print("Starting update process...")
    print()
    
    # Run the update
    success = update_server_urls()
    
    if success:
        print("\n✅ Update completed successfully!")
    else:
        print("\n❌ Update failed. Please check the errors above.")
        sys.exit(1)
