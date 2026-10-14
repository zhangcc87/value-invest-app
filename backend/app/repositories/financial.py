from collections.abc import Sequence
from datetime import date

from sqlmodel import Session, col, select

from app.models import FinancialReport
from app.repositories.upsert import bulk_upsert


def list_financials(*, session: Session, code: str) -> list[FinancialReport]:
    statement = (
        select(FinancialReport)
        .where(FinancialReport.code == code)
        .order_by(col(FinancialReport.stat_date))
    )
    return list(session.exec(statement).all())


def get_latest_financial(*, session: Session, code: str) -> FinancialReport | None:
    statement = (
        select(FinancialReport)
        .where(FinancialReport.code == code)
        .order_by(col(FinancialReport.stat_date).desc())
        .limit(1)
    )
    return session.exec(statement).first()


def existing_stat_dates(*, session: Session, code: str) -> set[date]:
    """Report periods already stored for `code`; the sync backfills the rest."""
    statement = select(col(FinancialReport.stat_date)).where(
        FinancialReport.code == code
    )
    return set(session.exec(statement).all())


def upsert_financials(*, session: Session, reports: Sequence[FinancialReport]) -> None:
    bulk_upsert(
        session=session,
        model=FinancialReport,
        rows=[report.model_dump() for report in reports],
        conflict_columns=["code", "stat_date"],
    )
