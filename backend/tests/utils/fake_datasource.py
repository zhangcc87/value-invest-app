"""In-memory `StockDataSource` so sync tests never touch the network."""

from collections.abc import Iterator, Sequence
from datetime import date, timedelta

from app.datasources.base import DailyBarRecord, FinancialRecord, StockRecord
from app.services.sync import quarter_end

# A stable, deliberately partial map: enough to prove the merge works without
# mirroring the real adapter's full field list.
_STATEMENT_COLUMNS: dict[str, tuple[str, ...]] = {
    "profit": ("roe_avg", "np_margin"),
    "growth": ("yoy_ni",),
    "balance": ("current_ratio",),
    "cashflow": ("cfo_to_np",),
    "operation": ("asset_turn_ratio",),
    "dupont": ("dupont_roe",),
}


def default_stocks() -> list[StockRecord]:
    return [
        StockRecord(
            code="sh.600519",
            symbol="600519",
            exchange="SH",
            board="主板",
            name="贵州茅台",
            industry="C15酒、饮料和精制茶制造业",
            sec_type=1,
            status=1,
            ipo_date=date(2001, 8, 27),
            out_date=None,
        ),
        StockRecord(
            code="sz.000001",
            symbol="000001",
            exchange="SZ",
            board="主板",
            name="平安银行",
            industry="J66货币金融服务",
            sec_type=1,
            status=1,
            ipo_date=date(1991, 4, 3),
            out_date=None,
        ),
    ]


class FakeDataSource:
    """Deterministic `StockDataSource`.

    Emits one bar per calendar day in the requested range, so continuation and
    idempotency assertions are exact. `fail_codes` raises for those codes to
    exercise the per-security failure path. Request logs let tests assert that
    the sync actually honored resume/dedup logic instead of re-fetching.
    """

    def __init__(
        self,
        *,
        stocks: list[StockRecord] | None = None,
        members: list[str] | None = None,
        periods_with_data: set[tuple[int, int]] | None = None,
        fail_codes: frozenset[str] = frozenset(),
    ) -> None:
        self.stocks = default_stocks() if stocks is None else stocks
        self.members = [s.code for s in self.stocks] if members is None else members
        self.periods_with_data = periods_with_data
        self.fail_codes = fail_codes
        self.daily_requests: list[tuple[str, date, date]] = []
        self.financial_requests: list[tuple[str, int, int]] = []

    def list_stocks(self) -> Iterator[StockRecord]:
        yield from self.stocks

    def list_index_members(self, *, index: str, as_of: date) -> Iterator[str]:
        yield from self.members

    def iter_daily_bars(
        self, *, code: str, start: date, end: date
    ) -> Iterator[DailyBarRecord]:
        self.daily_requests.append((code, start, end))
        if code in self.fail_codes:
            raise RuntimeError(f"fake failure for {code}")
        day = start
        price = 100.0
        while day <= end:
            yield DailyBarRecord(
                code=code,
                trade_date=day,
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                preclose=price,
                volume=1000.0,
                amount=100000.0,
                pct_chg=0.0,
                turn=0.1,
                tradestatus=1,
                is_st=0,
                pe_ttm=10.0,
                pb_mrq=1.0,
                ps_ttm=2.0,
                pcf_ncf_ttm=3.0,
            )
            day += timedelta(days=1)

    def query_financial(
        self,
        *,
        code: str,
        year: int,
        quarter: int,
        statements: Sequence[str],
    ) -> FinancialRecord | None:
        self.financial_requests.append((code, year, quarter))
        if code in self.fail_codes:
            raise RuntimeError(f"fake failure for {code}")
        if (
            self.periods_with_data is not None
            and (
                year,
                quarter,
            )
            not in self.periods_with_data
        ):
            return None
        stat_date = quarter_end(year, quarter)
        metrics = {
            column: 0.5 for name in statements for column in _STATEMENT_COLUMNS[name]
        }
        return FinancialRecord(
            code=code,
            stat_date=stat_date,
            pub_date=stat_date + timedelta(days=30),
            metrics=metrics,
        )
