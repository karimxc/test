from app.core.rate_scheduler import sync_rates_from_frankfurter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.exchange_rate_service import ExchangeRateService
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateUpdate, ExchangeRateResponse
from app.core.exceptions import ExchangeRateNotFoundError

router = APIRouter(prefix="/rates", tags=["Exchange Rates"])


@router.get("/", response_model=list[ExchangeRateResponse])
def list_rates(db: Session = Depends(get_db)):
    return ExchangeRateService(db).get_all()


@router.post("/", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_rate(data: ExchangeRateCreate, db: Session = Depends(get_db)):
    return ExchangeRateService(db).create_or_update(data)


@router.get("/{from_code}/{to_code}", response_model=ExchangeRateResponse)
def get_rate(from_code: str, to_code: str, db: Session = Depends(get_db)):
    try:
        return ExchangeRateService(db).get_rate(from_code, to_code)
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{from_code}/{to_code}", response_model=ExchangeRateResponse)
def update_rate(from_code: str, to_code: str, data: ExchangeRateUpdate, db: Session = Depends(get_db)):
    try:
        return ExchangeRateService(db).update(from_code, to_code, data)
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{from_code}/{to_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rate(from_code: str, to_code: str, db: Session = Depends(get_db)):
    try:
        ExchangeRateService(db).delete(from_code, to_code)
    except ExchangeRateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/sync", tags=["Exchange Rates"])
async def sync_rates():
    """Manually trigger a live rate sync from Frankfurter (ECB data)."""
    try:
        await sync_rates_from_frankfurter()
        return {"status": "ok", "message": "Rates synced from api.frankfurter.dev"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
