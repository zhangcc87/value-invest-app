"""Read-only stock queries (Phase 1: no writes outside the sync services)."""

from datetime import date

from fastapi import HTTPException
from sqlmodel import Session

from app.models import Stock
from app.repositories import financial as financial_repo
from app.repositories import quote as quote_repo
from app.repositories import stock as stock_repo
from app.schemas.stock import (
    DailyQuotePublic,
    FinancialReportPublic,
    StockPublic,
    StocksPublic,
)


def _require_stock(*, session: Session, code: str) -> Stock:
    stock = stock_repo.get_stock_by_code(session=session, code=code)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


def list_stocks(
    *,
    session: Session,
    page: int,
    size: int,
    board: str | None = None,
    industry: str | None = None,
    status: int | None = None,
    q: str | None = None,
) -> StocksPublic:
    count = stock_repo.count_stocks(
        session=session, board=board, industry=industry, status=status, q=q
    )
    rows = stock_repo.list_stocks(
        session=session,
        board=board,
        industry=industry,
        status=status,
        q=q,
        skip=(page - 1) * size,
        limit=size,
    )
    data = [StockPublic.model_validate(row, from_attributes=True) for row in rows]
    return StocksPublic(data=data, count=count)


def list_industries(*, session: Session) -> list[str]:
    return stock_repo.list_industries(session=session)


def read_stock(*, session: Session, code: str) -> StockPublic:
    return StockPublic.model_validate(
        _require_stock(session=session, code=code), from_attributes=True
    )


def read_quotes(
    *, session: Session, code: str, start: date | None, end: date | None
) -> list[DailyQuotePublic]:
    _require_stock(session=session, code=code)
    rows = quote_repo.list_quotes(session=session, code=code, start=start, end=end)
    return [DailyQuotePublic.model_validate(row, from_attributes=True) for row in rows]


def read_financials(*, session: Session, code: str) -> list[FinancialReportPublic]:
    _require_stock(session=session, code=code)
    rows = financial_repo.list_financials(session=session, code=code)
    return [
        FinancialReportPublic.model_validate(row, from_attributes=True) for row in rows
    ]
