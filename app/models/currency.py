from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Currency(Base):
    __tablename__ = "currencies"

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    stock = relationship("CurrencyStock", back_populates="currency", uselist=False, cascade="all, delete-orphan")
    rates_as_source = relationship("ExchangeRate", foreign_keys="ExchangeRate.from_currency_code", back_populates="from_currency")
    rates_as_target = relationship("ExchangeRate", foreign_keys="ExchangeRate.to_currency_code", back_populates="to_currency")
    transactions_as_source = relationship("Transaction", foreign_keys="Transaction.from_currency_code", back_populates="from_currency")
    transactions_as_target = relationship("Transaction", foreign_keys="Transaction.to_currency_code", back_populates="to_currency")
