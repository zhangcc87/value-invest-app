from collections.abc import Sequence
from datetime import date

from sqlmodel import Session, col, func, select

from app.models import DailyQuote
from app.repositories.upsert import bulk_upsert


def list_quotes(
    *,
    session: Session,
    code: str,
    start: date | None = None,
    end: date | None = None,
) -> list[DailyQuote]:
    statement = select(DailyQuote).where(DailyQuote.code == code)
    if start is not None:
        statement = statement.where(DailyQuote.trade_date >= start)
    if end is not None:
        statement = statement.where(DailyQuote.trade_date <= end)
    statement = statement.order_by(col(DailyQuote.trade_date))
    return list(session.exec(statement).all())


def max_trade_date(*, session: Session, code: str) -> date | None:
    """Latest stored bar for `code`; the daily sync resumes from here."""
    statement = select(func.max(DailyQuote.trade_date)).where(DailyQuote.code == code)
    return session.exec(statement).one()


def upsert_quotes(*, session: Session, quotes: Sequence[DailyQuote]) -> None:
    bulk_upsert(
        session=session,
        model=DailyQuote,
        rows=[quote.model_dump() for quote in quotes],
        conflict_columns=["code", "trade_date"],
    )
