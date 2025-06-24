from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import user_queries, uploads
import os

app = FastAPI()

# Replace with your actual Vercel URL (including scheme)
origins = [
    "https://audience-h1uu0w2ro-danrobuilds-projects.vercel.app",
    "https://www.audience-h1uu0w2ro-danrobuilds-projects.vercel.app",
    "https://audience-ai.vercel.app",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # exactly the domains you want to allow
    allow_credentials=True,           # if you need cookies/auth headers
    allow_methods=["*"],              # GET, POST, PUT, DELETE, OPTIONS…
    allow_headers=["*"],              # Authorization, Content-Type, etc.
)

# Mount routers
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(user_queries.router, prefix="/queries", tags=["queries"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ping")
async def ping():
    return {"ok": True}