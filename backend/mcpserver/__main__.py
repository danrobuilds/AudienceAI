# Start with cd backend, then python3 -m mcpserver

from .server import start_mcp_server

if __name__ == "__main__":
    print("Executing mcpserver package...")
    start_mcp_server() 