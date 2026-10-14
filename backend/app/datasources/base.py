from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class StockRecord:
    """One listed security from the source's master data."""

    code: str
    symbol: str
    exchange: str
    board: str
    name: str
    industry: str | None
    sec_type: int
    status: int
    ipo_date: date | None
    out_date: date | None


@dataclass(frozen=True)
class DailyBarRecord:
    """One trading day of price + valuation for a security."""

    code: str
    trade_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    preclose: float | None
    volume: float | None
    amount: float | None
    pct_chg: float | None
    turn: float | None
    tradestatus: int | None
    is_st: int | None
    pe_ttm: float | None
    pb_mrq: float | None
    ps_ttm: float | None
    pcf_ncf_ttm: float | None


@dataclass(frozen=True)
class FinancialRecord:
    """One report period, metrics keyed by column name.

    `metrics` covers only the statements requested, so a period can be stored
    incrementally: `FinancialReport` columns default to None for the rest.
    Ratios are decimals (0.3446 == 34.46%).
    """

    code: str
    stat_date: date
    pub_date: date | None
    metrics: dict[str, float | None]


class StockDataSource(Protocol):
    """External market-data source. Implementations own all network IO.

    The sync services depend on this Protocol, never on a concrete vendor, so
    tests inject an in-memory fake and never touch the network.
    """

    def list_stocks(self) -> Iterator[StockRecord]:
        """Master data for every listed security, with industry where known."""
        ...

    def list_index_members(self, *, index: str, as_of: date) -> Iterator[str]:
        """Constituent codes of `index` (e.g. "hs300") as of `as_of`."""
        ...

    def iter_daily_bars(
        self, *, code: str, start: date, end: date
    ) -> Iterator[DailyBarRecord]:
        """Trading days in `[start, end]` for one security (unadjusted)."""
        ...

    def query_financial(
        self,
        *,
        code: str,
        year: int,
        quarter: int,
        statements: Sequence[str],
    ) -> FinancialRecord | None:
        """Merge the requested statements for one period, or None if absent."""
        ...
