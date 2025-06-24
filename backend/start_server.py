#!/usr/bin/env python3
"""
Simple startup script for the AudienceAI FastAPI backend.
"""

import uvicorn
import os

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🚀 Starting AudienceAI FastAPI server on http://{host}:{port}")
    print("📝 Available endpoints:")
    print("   • http://localhost:8000/health - Health check")
    print("   • http://localhost:8000/queries/generate - Generate content")
    print("   • http://localhost:8000/queries/generate-stream - Generate with streaming")
    print("   • http://localhost:8000/uploads/ - File uploads")
    print("   • http://localhost:8000/docs - API documentation")
    print()
    
    # Start the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    ) 