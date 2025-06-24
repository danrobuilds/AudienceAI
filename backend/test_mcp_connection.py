#!/usr/bin/env python3
"""
Test script to diagnose MCP connection issues on Railway
"""

import asyncio
import os
import sys
import traceback

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_mcp_connection():
    """Test MCP server connection with detailed error reporting"""
    
    # Test different connection URLs
    test_urls = [
        "http://127.0.0.1:8050/sse",
        "http://localhost:8050/sse",
        "http://0.0.0.0:8050/sse",
    ]
    
    for url in test_urls:
        print(f"\n🔧 Testing connection to: {url}")
        
        try:
            async with sse_client(url) as (read_stream, write_stream):
                print(f"✅ SSE client connected successfully")
                
                async with ClientSession(read_stream, write_stream) as session:
                    print(f"✅ ClientSession created successfully")
                    
                    # Try to initialize
                    await asyncio.wait_for(session.initialize(), timeout=10.0)
                    print(f"✅ Session initialized successfully")
                    
                    # Try to call a simple tool
                    response = await session.call_tool("search_recent_news", arguments={"query": "test", "sort_by": "relevancy"})
                    print(f"✅ Tool call successful: {type(response)}")
                    
                    return True
                    
        except Exception as e:
            print(f"❌ Connection failed: {type(e).__name__}: {e}")
            print(f"📊 Full traceback:")
            traceback.print_exc()
            continue
    
    return False

async def main():
    """Main test function"""
    print("🧪 MCP Connection Test for Railway")
    print("=" * 50)
    
    # Check if MCP server is running
    import socket
    try:
        with socket.create_connection(("127.0.0.1", 8050), timeout=5):
            print("✅ MCP server port is open")
    except Exception as e:
        print(f"❌ MCP server port is not accessible: {e}")
        return
    
    # Test the connection
    success = await test_mcp_connection()
    
    if success:
        print("\n🎉 MCP connection test PASSED")
    else:
        print("\n💥 MCP connection test FAILED")

if __name__ == "__main__":
    asyncio.run(main()) 