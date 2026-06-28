from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.stock_service import StockService
from app.schemas.stock import StockResponse, StockAdjust
from app.core.exceptions import CurrencyNotFoundError, InsufficientStockError

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("/", response_model=list[StockResponse])
def list_stock(db: Session = Depends(get_db)):
    return StockService(db).get_all()


@router.get("/{currency_code}", response_model=StockResponse)
def get_stock(currency_code: str, db: Session = Depends(get_db)):
    try:
        return StockService(db).get_by_code(currency_code)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{currency_code}/deposit", response_model=StockResponse)
def deposit(currency_code: str, data: StockAdjust, db: Session = Depends(get_db)):
    try:
        result = StockService(db).deposit(currency_code, data.amount)
        db.commit()  # commit here since we're outside TransactionService
        db.refresh(result)
        return result
    except CurrencyNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{currency_code}/withdraw", response_model=StockResponse)
def withdraw(currency_code: str, data: StockAdjust, db: Session = Depends(get_db)):
    try:
        result = StockService(db).withdraw(currency_code, data.amount)
        db.commit()
        db.refresh(result)
        return result
    except CurrencyNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
