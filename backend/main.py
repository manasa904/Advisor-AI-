from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import os

# Existing routers
from app.api.chat import router as chat_router
from app.api.portfolio import router as portfolio_router
from app.api.compliance import router as compliance_router
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router

# New routers
from app.api.revenue_api import router as revenue_router
from app.api.analytics_api import router as analytics_router
from app.api.governance_api import router as governance_router
from app.api.metrics_api import router as metrics_router
from app.api.metrics_api import knowledge_router

load_dotenv()

# CREATE FASTAPI APP FIRST
app = FastAPI(
    title="Advisor AI API",
    version="1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routes
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(chat_router, prefix="/api/v1/chat")
app.include_router(portfolio_router, prefix="/api/v1/portfolio")
app.include_router(compliance_router, prefix="/api/v1/compliance")
app.include_router(alerts_router, prefix="/api/v1/alerts")

# New AI/Analytics routes
app.include_router(revenue_router)
app.include_router(analytics_router)
app.include_router(governance_router)
app.include_router(metrics_router)
app.include_router(knowledge_router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Advisor AI API is running"}

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}