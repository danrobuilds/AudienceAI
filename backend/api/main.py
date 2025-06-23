from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import user_queries, uploads

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
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