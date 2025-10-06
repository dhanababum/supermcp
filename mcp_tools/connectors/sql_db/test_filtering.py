#!/usr/bin/env python3
"""
Test script to demonstrate user-based tool filtering in the MCP server.
This script shows how tools are filtered based on the authenticated user.
"""

import requests
import json

# Test token from the server output (update this with the latest token from server startup)
TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiaXNzIjoiaHR0cHM6Ly90ZXN0LnlvdXJjb21wYW55LmNvbSIsImlhdCI6MTc1OTU0MjIzOCwiZXhwIjoxNzU5NTQ1ODM4LCJhdWQiOiJ0ZXN0LW1jcC1zZXJ2ZXIiLCJzY29wZSI6InJlYWQgd3JpdGUgYWRtaW4ifQ.rFhnPULR_2aatSWGbbmm9ucjmgLzr7OQGdnRiCo9qpA8ULLSnppEFiBlBBvAvLAtpVskx-dsJloqUb4kKpYamVQECra8USYGXh_lcMcevg2ObV-vyIgeQUQ2S_kTw7Hmmq7kgZvthxuRQQ2l3E0Tmc5LFDSXJufErV6qe1lqOgarXkiJfxnlBwGxKTo7mMiL1_0STbGDp1MPZGVdNRjWjeUhhvPuMYP5c4gzM-0alMLem1gp50pIWyAgNnoRmtcTUqA2cS7c2dO2Mxvy8r-IhtbmTq8LeBxMQGZrXhoJiK6Rk-8i_oCxMPpDslGf57JTIAnZn4pVMEHKjx_SQFQUGA"

def test_tool_listing():
    """Test listing tools with JWT authentication."""
    print("🔍 Testing tool listing with JWT authentication...")
    
    url = "http://127.0.0.1:8015/mcp"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # MCP tools/list request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                print(f"✅ Found {len(tools)} tools for authenticated user:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
            else:
                print(f"❌ Unexpected response format: {data}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        print("💡 Make sure the MCP server is running: python new_mcp.py")

def test_tool_call():
    """Test calling a tool with JWT authentication."""
    print("\n🔧 Testing tool call with JWT authentication...")
    
    url = "http://127.0.0.1:8015/mcp"
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # MCP tools/call request
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "test-user-123__echo",
            "arguments": {
                "payload": {"message": "Hello from JWT user!"}
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                print(f"✅ Tool call successful: {data['result']}")
            else:
                print(f"❌ Tool call failed: {data}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

def test_unauthorized_access():
    """Test accessing tools without authentication."""
    print("\n🚫 Testing unauthorized access...")
    
    url = "http://127.0.0.1:8015/mcp"
    headers = {
        "Content-Type": "application/json"
    }
    
    # MCP tools/list request without auth
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                print(f"🔒 Unauthorized access returned {len(tools)} tools (should be 0)")
                if len(tools) == 0:
                    print("✅ Security working: No tools returned for unauthorized user")
                else:
                    print("❌ Security issue: Tools returned for unauthorized user")
            else:
                print(f"❌ Unexpected response format: {data}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")

if __name__ == "__main__":
    print("🧪 Testing MCP Server User-Based Tool Filtering")
    print("=" * 50)
    
    test_tool_listing()
    test_tool_call()
    test_unauthorized_access()
    
    print("\n✨ Test completed!")
    print("\n💡 To run the MCP server: python new_mcp.py")
    print("💡 Then run this test: python test_filtering.py")
