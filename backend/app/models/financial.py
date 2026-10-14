from datetime import date

from sqlmodel import Field

from app.schemas.stock import FinancialReportBase


class FinancialReport(FinancialReportBase, table=True):
    """Quarterly financials, one wide row per (code, stat_date).

    Columns cover all six baostock statement queries; the sync fills only the
    enabled ones, so enabling cash-flow/operation/dupont later needs no
    migration. Ratios are stored as decimals (roe_avg=0.3446 == 34.46%).
    """

    code: str = Field(
        max_length=16,
        foreign_key="stock.code",
        ondelete="CASCADE",
        primary_key=True,
    )
    stat_date: date = Field(primary_key=True)
