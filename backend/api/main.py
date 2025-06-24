from fastapi import FastAPI
from api.routes import user_queries, uploads
import os

app = FastAPI()

# Mount routers
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(user_queries.router, prefix="/queries", tags=["queries"])

@app.get("/health")
async def health():
    return {"status": "ok"}