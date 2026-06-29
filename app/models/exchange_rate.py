from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(String(36), primary_key=True)
    from_currency_code = Column(String(10), ForeignKey("currencies.code"), nullable=False)
    to_currency_code = Column(String(10), ForeignKey("currencies.code"), nullable=False)
    rate = Column(Numeric(precision=18, scale=8), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("from_currency_code", "to_currency_code", name="uq_exchange_rate_pair"),
    )

    # Relationships
    from_currency = relationship("Currency", foreign_keys=[from_currency_code], back_populates="rates_as_source")
    to_currency = relationship("Currency", foreign_keys=[to_currency_code], back_populates="rates_as_target")
