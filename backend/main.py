from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

import os
load_dotenv()

from routers import transactions, analytics, upload, ai

app = FastAPI(title="Vantge API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated Rate Limiting Headers Middleware
@app.middleware("http")
async def add_rate_limit_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["X-RateLimit-Reset"] = "60000"
    return response

# Include routers
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/api/health")
def health_check():
    from datetime import datetime
    return {
        "status": "ok",
        "message": "Vantge API is running (Python)",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
