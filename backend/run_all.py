import asyncio
import os
import sys
import uvicorn

# Add project root to Python path to fix relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now import with correct path structure
from backend.api.main import app

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
    
    # Use subprocess to run MCP server as separate process
    mcp_process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "backend.mcpserver",
        cwd=project_root,  # Run from project root
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    print(f"MCP Server started with PID: {mcp_process.pid}")
    
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