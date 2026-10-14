from datetime import date
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, get_current_active_superuser
from app.schemas.stock import (
    DailyQuotePublic,
    FinancialReportPublic,
    StockPublic,
    StocksPublic,
    SyncRunsPublic,
)
from app.services import stock as stock_service
from app.services import sync as sync_service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/", response_model=StocksPublic)
def read_stocks(
    session: SessionDep,
    page: int = 1,
    size: int = 20,
    board: str | None = None,
    industry: str | None = None,
    status: int | None = None,
    q: str | None = None,
) -> Any:
    """List stocks with optional filters; `q` matches code/symbol/name."""
    return stock_service.list_stocks(
        session=session,
        page=page,
        size=size,
        board=board,
        industry=industry,
        status=status,
        q=q,
    )


@router.get(
    "/sync/runs",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SyncRunsPublic,
)
def read_sync_runs(session: SessionDep, page: int = 1, size: int = 20) -> Any:
    """Sync history, most recent first (superuser only)."""
    return sync_service.list_sync_runs(
        session=session, skip=(page - 1) * size, limit=size
    )


@router.get("/industries", response_model=list[str])
def read_industries(session: SessionDep) -> Any:
    """Distinct industries present in the master data (list-page filter).

    Declared before `/{code}` so "industries" is not captured as a code.
    """
    return stock_service.list_industries(session=session)


@router.get("/{code}", response_model=StockPublic)
def read_stock(code: str, session: SessionDep) -> Any:
    """One stock by baostock code, e.g. `sh.600519`."""
    return stock_service.read_stock(session=session, code=code)


@router.get("/{code}/quotes", response_model=list[DailyQuotePublic])
def read_stock_quotes(
    code: str,
    session: SessionDep,
    start: date | None = None,
    end: date | None = None,
) -> Any:
    """Daily price + valuation series, ascending by trade date."""
    return stock_service.read_quotes(session=session, code=code, start=start, end=end)


@router.get("/{code}/financials", response_model=list[FinancialReportPublic])
def read_stock_financials(code: str, session: SessionDep) -> Any:
    """Quarterly financial series (ratios are decimals; `pub_date` is PIT)."""
    return stock_service.read_financials(session=session, code=code)
