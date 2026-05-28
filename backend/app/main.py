from app.api.revenue_api import router as revenue_router
from app.api.analytics_api import router as analytics_router
from app.api.governance_api import router as governance_router
from app.api.metrics_api import router as metrics_router
from app.api.metrics_api import knowledge_router

app.include_router(revenue_router)
app.include_router(analytics_router)
app.include_router(governance_router)
app.include_router(metrics_router)
app.include_router(knowledge_router)