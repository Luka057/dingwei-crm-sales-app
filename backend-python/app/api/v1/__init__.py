"""/api/v1 路由聚合。"""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    auth,
    customers,
    health,
    manager,
    plans,
    transfers,
    uploads,
    visit_records,
    weekly_reports,
)

api_router = APIRouter()
# 公开
api_router.include_router(health.router)
api_router.include_router(auth.router)
# 业务(需 JWT)
api_router.include_router(customers.router)
api_router.include_router(plans.router)
api_router.include_router(visit_records.router)
api_router.include_router(uploads.router)
api_router.include_router(weekly_reports.router)
api_router.include_router(transfers.router)
# Manager-only
api_router.include_router(manager.router)
# AI(全 stub,带 JWT)
api_router.include_router(ai.router)
