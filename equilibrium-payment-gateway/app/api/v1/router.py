from fastapi import APIRouter

from app.api.v1.endpoints import auth, members, plans, subscriptions, payments

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",          tags=["Auth"])
api_router.include_router(members.router,       prefix="/members",       tags=["Members"])
api_router.include_router(plans.router,         prefix="/plans",         tags=["Plans"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(payments.router,      prefix="/payments",      tags=["Payments"])
