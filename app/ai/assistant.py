from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session
from app.services.dashboard_service import DashboardService
from app.services.transaction_service import TransactionService
from app.core.config import settings
import json
from decimal import Decimal


SYSTEM_PROMPT = """You are an operational assistant for a currency exchange bureau.
You receive structured data about current inventory, transactions, and exchange rates,
and your job is to answer the operator's natural language questions clearly and concisely.

Rules:
- Never make or suggest business decisions on behalf of the system.
- Never modify, create, or delete any data.
- Only describe, summarize, or explain what the data shows.
- Be precise with numbers and currency codes.
- Keep responses short and professional.
"""


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class AIAssistant:

    def __init__(self, db: Session):
        self.db = db
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY,
            temperature=0.2,
        )

    def _build_context(self) -> str:
        dashboard_service = DashboardService(self.db)
        tx_service = TransactionService(self.db)

        overview = dashboard_service.get_overview()
        today_txs = tx_service.get_today()

        context = {
            "balances": [
                {"currency": b.currency_code, "balance": float(b.balance)}
                for b in overview.balances
            ],
            "today": {
                "transaction_count": overview.total_transactions_today,
                "total_volume": float(overview.total_volume_today),
                "transactions": [
                    {
                        "id": tx.id,
                        "from": tx.from_currency_code,
                        "to": tx.to_currency_code,
                        "amount": float(tx.amount),
                        "converted": float(tx.converted_amount),
                        "rate": float(tx.rate),
                        "type": tx.operation_type.value,
                        "time": tx.created_at.isoformat(),
                    }
                    for tx in today_txs
                ],
            },
            "active_currencies": overview.active_currencies,
            "total_currencies": overview.total_currencies,
        }
        return json.dumps(context, default=_decimal_default, indent=2)

    def query(self, user_question: str) -> str:
        context_json = self._build_context()

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Current system data:\n{context_json}\n\nOperator question: {user_question}"
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content
