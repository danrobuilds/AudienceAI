from fastapi import FastAPI
from api.routes import chat, tools, user_queries
from backend.api.routes import uploads

app = FastAPI()

# Mount routers
app.include_router(uploads.router, prefix="/documents", tags=["documents"])
app.include_router(user_queries.router, prefix="/queries", tags=["queries"])

@app.get("/health")
async def health():
    return {"status": "ok"}