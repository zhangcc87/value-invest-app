from datetime import date

from sqlmodel import Field

from app.schemas.stock import DailyQuoteBase


class DailyQuote(DailyQuoteBase, table=True):
    """Daily OHLC + valuation. Composite PK `(code, trade_date)`.

    Natural key lets the sync write with `INSERT ... ON CONFLICT DO UPDATE`,
    making repeated runs idempotent without a separate progress table.
    """

    code: str = Field(
        max_length=16,
        foreign_key="stock.code",
        ondelete="CASCADE",
        primary_key=True,
    )
    trade_date: date = Field(primary_key=True)
