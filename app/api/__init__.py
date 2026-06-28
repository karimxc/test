from fastapi import APIRouter
from app.api.routes import currencies, stock, rates, transactions, dashboard, ai

api_router = APIRouter()

api_router.include_router(currencies.router)
api_router.include_router(stock.router)
api_router.include_router(rates.router)
api_router.include_router(transactions.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
