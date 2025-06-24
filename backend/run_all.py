import asyncio
import os
import sys
import uvicorn

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import with consistent path since we always run from backend directory
from api.main import app

async def start_api():
    """Start the FastAPI server with async-compatible configuration"""
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=int(os.environ.get("PORT", 8000)),
        reload=False,  # Disable reload for production
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def start_mcp():
    """Start the MCP server using async subprocess"""
    import subprocess
    
    # Try different module paths for MCP server
    mcp_module_options = ["mcpserver", "backend.mcpserver"]
    
    for module_path in mcp_module_options:
        try:
            # Use subprocess to run MCP server as separate process
            mcp_process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", module_path,
                cwd=current_dir if module_path == "mcpserver" else current_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            print(f"MCP Server started with PID: {mcp_process.pid} using module: {module_path}")
            break
        except Exception as e:
            print(f"Failed to start MCP server with {module_path}: {e}")
            if module_path == mcp_module_options[-1]:  # Last attempt failed
                raise
    
    # Monitor the process
    try:
        await mcp_process.wait()
    except Exception as e:
        print(f"MCP Server error: {e}")
        if mcp_process.returncode is None:
            mcp_process.terminate()
            await mcp_process.wait()

async def main():
    """Start both servers concurrently for Railway deployment"""
    print("🚀 Starting AudienceAI servers for Railway...")
    print(f"🌐 FastAPI will run on: http://0.0.0.0:{os.environ.get('PORT', 8000)}")
    print("🔧 MCP Server will run on: http://0.0.0.0:8050")
    
    # Set environment variables for MCP server communication in Railway
    if not os.getenv("MCP_SERVER_HOST"):
        os.environ["MCP_SERVER_HOST"] = "127.0.0.1"  # Use localhost for internal communication
    if not os.getenv("MCP_SERVER_PORT"):
        os.environ["MCP_SERVER_PORT"] = "8050"
    
    print(f"🔧 MCP Client will connect to: http://{os.environ.get('MCP_SERVER_HOST', '127.0.0.1')}:{os.environ.get('MCP_SERVER_PORT', '8050')}/sse")
    
    try:
        # Start both servers concurrently
        await asyncio.gather(
            start_api(),
            start_mcp(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        print("🛑 Shutting down servers...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    # Set event loop policy for better compatibility
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())