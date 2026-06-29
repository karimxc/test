from contextlib import asynccontextmanager
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api import api_router
from app.core.exceptions import (
    CurrencyNotFoundError,
    CurrencyInactiveError,
    InsufficientStockError,
    ExchangeRateNotFoundError,
    DuplicateCurrencyError,
)
from app.core.rate_scheduler import (
    start_rate_scheduler,
    stop_rate_scheduler,
    sync_rates_from_frankfurter,
)

logging.basicConfig(level=logging.INFO)

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await sync_rates_from_frankfurter()
    start_rate_scheduler()
    yield
    stop_rate_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    description=(
        "Internal system for managing currency exchange operations. "
        "Tracks inventory, records buy/sell transactions, manages exchange rates, "
        "and provides AI-assisted operational insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Exception handlers ─────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers=CORS_HEADERS,
    )

@app.exception_handler(CurrencyNotFoundError)
async def currency_not_found_handler(request: Request, exc: CurrencyNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)}, headers=CORS_HEADERS)

@app.exception_handler(DuplicateCurrencyError)
async def duplicate_currency_handler(request: Request, exc: DuplicateCurrencyError):
    return JSONResponse(status_code=409, content={"detail": str(exc)}, headers=CORS_HEADERS)

@app.exception_handler(CurrencyInactiveError)
async def currency_inactive_handler(request: Request, exc: CurrencyInactiveError):
    return JSONResponse(status_code=422, content={"detail": str(exc)}, headers=CORS_HEADERS)

@app.exception_handler(InsufficientStockError)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=422, content={"detail": str(exc)}, headers=CORS_HEADERS)

@app.exception_handler(ExchangeRateNotFoundError)
async def exchange_rate_not_found_handler(request: Request, exc: ExchangeRateNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)}, headers=CORS_HEADERS)

# ── API Routes ─────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")

# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

# ── Frontend static files ──────────────────────────────────────────────────────
# Serve frontend/ directory — index.html at root, config.js alongside it
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", tags=["Frontend"])
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    @app.get("/", tags=["Health"])
    def root():
        return {"status": "ok", "app": settings.APP_NAME}
