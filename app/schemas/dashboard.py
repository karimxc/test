from decimal import Decimal
from pydantic import BaseModel
from app.schemas.stock import StockResponse
from app.schemas.transaction import TransactionResponse


class DashboardResponse(BaseModel):
    total_currencies: int
    active_currencies: int
    total_transactions_today: int
    total_volume_today: Decimal
    balances: list[StockResponse]
    recent_transactions: list[TransactionResponse]
