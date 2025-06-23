from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import user_queries, uploads
import os

app = FastAPI()

# Add CORS middleware - allow all origins for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Mount routers
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(user_queries.router, prefix="/queries", tags=["queries"])

@app.get("/health")
async def health():
    return {"status": "ok"}