from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.core.exceptions import (
    CurrencyNotFoundError,
    CurrencyInactiveError,
    InsufficientStockError,
    ExchangeRateNotFoundError,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=list[TransactionResponse])
def list_transactions(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return TransactionService(db).get_all(limit=limit, offset=offset)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def execute_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    try:
        return TransactionService(db).execute(data)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CurrencyInactiveError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/today", response_model=list[TransactionResponse])
def today_transactions(db: Session = Depends(get_db)):
    return TransactionService(db).get_today()


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    try:
        return TransactionService(db).get_by_id(transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
