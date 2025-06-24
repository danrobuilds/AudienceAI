import asyncio
import os
import sys
import uvicorn
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import with consistent path since we always run from backend directory
from api.main import app
from mcpserver.server import start_mcp_server

def run_mcp_server():
    """Run MCP server in a separate thread"""
    print("🔧 Starting MCP Server in thread...")
    try:
        start_mcp_server()
    except Exception as e:
        print(f"❌ MCP Server error: {e}")

async def start_api_server():
    """Start the FastAPI server"""
    print("🌐 Starting FastAPI server...")
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

def main():
    """Start both servers using threading approach"""
    print("🚀 Starting AudienceAI servers for Railway (threaded approach)...")
    print(f"🌐 FastAPI will run on: http://0.0.0.0:{os.environ.get('PORT', 8000)}")
    print("🔧 MCP Server will run on: http://0.0.0.0:8050")
    
    # Set environment variables for MCP server communication
    if not os.getenv("MCP_SERVER_HOST"):
        os.environ["MCP_SERVER_HOST"] = "127.0.0.1"
    if not os.getenv("MCP_SERVER_PORT"):
        os.environ["MCP_SERVER_PORT"] = "8050"
    
    print(f"🔧 MCP Client will connect to: http://{os.environ.get('MCP_SERVER_HOST')}:{os.environ.get('MCP_SERVER_PORT')}/sse")
    
    try:
        # Start MCP server in a separate thread
        mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
        mcp_thread.start()
        
        # Give MCP server time to start
        print("⏳ Waiting for MCP server to start...")
        time.sleep(5)
        
        # Start FastAPI server in main thread
        asyncio.run(start_api_server())
        
    except KeyboardInterrupt:
        print("🛑 Shutting down servers...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    main() 