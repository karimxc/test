import enum
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class OperationType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    from_currency_code = Column(String(10), ForeignKey("currencies.code"), nullable=False)
    to_currency_code = Column(String(10), ForeignKey("currencies.code"), nullable=False)
    amount = Column(Numeric(precision=18, scale=4), nullable=False)
    converted_amount = Column(Numeric(precision=18, scale=4), nullable=False)
    rate = Column(Numeric(precision=18, scale=8), nullable=False)
    operation_type = Column(
        Enum(OperationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    from_currency = relationship("Currency", foreign_keys=[from_currency_code], back_populates="transactions_as_source")
    to_currency = relationship("Currency", foreign_keys=[to_currency_code], back_populates="transactions_as_target")
