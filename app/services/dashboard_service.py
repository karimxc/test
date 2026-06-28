from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.currency import Currency
from app.schemas.dashboard import DashboardResponse
from app.services.stock_service import StockService
from app.services.transaction_service import TransactionService


class DashboardService:

    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.transaction_service = TransactionService(db)

    def get_overview(self) -> DashboardResponse:
        all_currencies = self.db.query(Currency).all()
        active_currencies = [c for c in all_currencies if c.is_active]
        balances = self.stock_service.get_all()
        today_transactions = self.transaction_service.get_today()
        recent_transactions = self.transaction_service.get_all(limit=10)

        total_volume_today = sum(
            Decimal(str(tx.amount)) for tx in today_transactions
        )

        return DashboardResponse(
            total_currencies=len(all_currencies),
            active_currencies=len(active_currencies),
            total_transactions_today=len(today_transactions),
            total_volume_today=total_volume_today,
            balances=balances,
            recent_transactions=recent_transactions,
        )
