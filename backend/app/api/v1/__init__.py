from fastapi import APIRouter

from app.api.v1 import admin, auth, invites, markets, me, orders

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(invites.router)
router.include_router(admin.router)
router.include_router(me.router)
router.include_router(markets.router)
router.include_router(orders.router)
