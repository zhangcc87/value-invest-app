import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.base import get_datetime_utc


class SyncRun(SQLModel, table=True):
    """Bookkeeping row per sync invocation (dataset = stock_list|daily|financial)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dataset: str = Field(max_length=16)
    scope: str | None = Field(default=None, max_length=32)
    started_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    status: str = Field(default="running", max_length=16)  # running|success|failed
    total: int | None = None
    processed: int | None = None
    failed: int | None = None
    last_error: str | None = None
    params: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
