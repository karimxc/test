from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class CurrencyStock(Base):
    __tablename__ = "currency_stocks"

    currency_code = Column(String(10), ForeignKey("currencies.code"), primary_key=True)
    balance = Column(Numeric(precision=18, scale=4), nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    currency = relationship("Currency", back_populates="stock")
