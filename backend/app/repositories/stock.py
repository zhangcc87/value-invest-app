from collections.abc import Sequence

from sqlalchemy import ColumnElement, or_
from sqlmodel import Session, col, func, select

from app.models import Stock
from app.repositories.upsert import bulk_upsert


def get_stock_by_code(*, session: Session, code: str) -> Stock | None:
    return session.get(Stock, code)


def list_all_codes(*, session: Session, status: int | None = 1) -> list[str]:
    """Every stored code, optionally filtered by listing status (`1` listed)."""
    statement = select(col(Stock.code))
    if status is not None:
        statement = statement.where(col(Stock.status) == status)
    statement = statement.order_by(col(Stock.code))
    return list(session.exec(statement).all())


def list_industries(*, session: Session) -> list[str]:
    """Distinct, non-null industries, sorted — feeds the list-page filter."""
    statement = (
        select(col(Stock.industry))
        .where(col(Stock.industry).is_not(None))
        .distinct()
        .order_by(col(Stock.industry))
    )
    return [industry for industry in session.exec(statement).all() if industry]


def _filters(
    *,
    board: str | None,
    industry: str | None,
    status: int | None,
    q: str | None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if board is not None:
        conditions.append(col(Stock.board) == board)
    if industry is not None:
        conditions.append(col(Stock.industry) == industry)
    if status is not None:
        conditions.append(col(Stock.status) == status)
    if q:
        pattern = f"%{q}%"
        conditions.append(
            or_(
                col(Stock.code).ilike(pattern),
                col(Stock.symbol).ilike(pattern),
                col(Stock.name).ilike(pattern),
            )
        )
    return conditions


def list_stocks(
    *,
    session: Session,
    board: str | None = None,
    industry: str | None = None,
    status: int | None = None,
    q: str | None = None,
    skip: int,
    limit: int,
) -> list[Stock]:
    statement = select(Stock)
    conditions = _filters(board=board, industry=industry, status=status, q=q)
    if conditions:
        statement = statement.where(*conditions)
    statement = statement.order_by(col(Stock.code)).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def count_stocks(
    *,
    session: Session,
    board: str | None = None,
    industry: str | None = None,
    status: int | None = None,
    q: str | None = None,
) -> int:
    statement = select(func.count()).select_from(Stock)
    conditions = _filters(board=board, industry=industry, status=status, q=q)
    if conditions:
        statement = statement.where(*conditions)
    return session.exec(statement).one()


def upsert_stocks(*, session: Session, stocks: Sequence[Stock]) -> None:
    bulk_upsert(
        session=session,
        model=Stock,
        rows=[stock.model_dump() for stock in stocks],
        conflict_columns=["code"],
    )
