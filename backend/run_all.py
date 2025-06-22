import asyncio
from mcpserver.server import start_mcp
from api.main import app
import uvicorn

async def main():
    mcp_task = asyncio.create_task(start_mcp())
    api_task = asyncio.create_task(uvicorn.run(app, host="0.0.0.0", port=int(os.environ["PORT"])))
    await asyncio.gather(mcp_task, api_task)

if __name__ == "__main__":
    asyncio.run(main())