from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field

from app.models.base import get_datetime_utc
from app.schemas.stock import StockBase


class Stock(StockBase, table=True):
    """A-share master data. Natural PK: baostock `code` (e.g. "sh.600519")."""

    code: str = Field(max_length=16, primary_key=True)
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
