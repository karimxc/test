from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.currency_service import CurrencyService
from app.schemas.currency import CurrencyCreate, CurrencyUpdate, CurrencyResponse
from app.core.exceptions import CurrencyNotFoundError, DuplicateCurrencyError

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.get("/", response_model=list[CurrencyResponse])
def list_currencies(db: Session = Depends(get_db)):
    return CurrencyService(db).get_all()


@router.post("/", response_model=CurrencyResponse, status_code=status.HTTP_201_CREATED)
def create_currency(data: CurrencyCreate, db: Session = Depends(get_db)):
    try:
        return CurrencyService(db).create(data)
    except DuplicateCurrencyError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{code}", response_model=CurrencyResponse)
def get_currency(code: str, db: Session = Depends(get_db)):
    try:
        return CurrencyService(db).get_by_code(code)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{code}", response_model=CurrencyResponse)
def update_currency(code: str, data: CurrencyUpdate, db: Session = Depends(get_db)):
    try:
        return CurrencyService(db).update(code, data)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(code: str, db: Session = Depends(get_db)):
    try:
        CurrencyService(db).delete(code)
    except CurrencyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
