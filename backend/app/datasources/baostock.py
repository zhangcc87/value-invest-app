import contextlib
import io
import logging
import time
from collections.abc import Callable, Iterator, Sequence
from datetime import date
from types import TracebackType
from typing import Any, Self

import baostock as bs

from app.core.config import settings
from app.datasources.base import DailyBarRecord, FinancialRecord, StockRecord

logger = logging.getLogger(__name__)

# Unadjusted daily bars + valuation (adjustflag="3" == no adjustment). The
# returned columns always include `code`; rows are read by field name.
_K_FIELDS = (
    "date,code,open,high,low,close,preclose,volume,amount,pctChg,turn,"
    "tradestatus,isST,peTTM,pbMRQ,psTTM,pcfNcfTTM"
)

# statement key -> (baostock query function, {raw field: column name})
_STATEMENTS: dict[str, tuple[str, dict[str, str]]] = {
    "profit": (
        "query_profit_data",
        {
            "roeAvg": "roe_avg",
            "npMargin": "np_margin",
            "gpMargin": "gp_margin",
            "netProfit": "net_profit",
            "epsTTM": "eps_ttm",
            "MBRevenue": "mb_revenue",
            "totalShare": "total_share",
            "liqaShare": "liqa_share",
        },
    ),
    "growth": (
        "query_growth_data",
        {
            "YOYEquity": "yoy_equity",
            "YOYAsset": "yoy_asset",
            "YOYNI": "yoy_ni",
            "YOYEPSBasic": "yoy_eps_basic",
            "YOYPNI": "yoy_pni",
        },
    ),
    "balance": (
        "query_balance_data",
        {
            "currentRatio": "current_ratio",
            "quickRatio": "quick_ratio",
            "cashRatio": "cash_ratio",
            "YOYLiability": "yoy_liability",
            "liabilityToAsset": "liability_to_asset",
            "assetToEquity": "asset_to_equity",
        },
    ),
    "cashflow": (
        "query_cash_flow_data",
        {
            "CAToAsset": "cato_asset",
            "NCAToAsset": "ncato_asset",
            "tangibleAssetToAsset": "tangible_asset_to_asset",
            "ebitToInterest": "ebit_to_interest",
            "CFOToOR": "cfo_to_or",
            "CFOToNP": "cfo_to_np",
            "CFOToGr": "cfo_to_gr",
        },
    ),
    "operation": (
        "query_operation_data",
        {
            "NRTurnRatio": "nr_turn_ratio",
            "NRTurnDays": "nr_turn_days",
            "INVTurnRatio": "inv_turn_ratio",
            "INVTurnDays": "inv_turn_days",
            "CATurnRatio": "ca_turn_ratio",
            "AssetTurnRatio": "asset_turn_ratio",
        },
    ),
    "dupont": (
        "query_dupont_data",
        {
            "dupontROE": "dupont_roe",
            "dupontAssetStoEquity": "dupont_asset_sto_equity",
            "dupontAssetTurn": "dupont_asset_turn",
            "dupontPnitoni": "dupont_pnitoni",
            "dupontNitogr": "dupont_nitogr",
            "dupontTaxBurden": "dupont_tax_burden",
            "dupontIntburden": "dupont_intburden",
            "dupontEbittogr": "dupont_ebittogr",
        },
    ),
}

STATEMENTS: tuple[str, ...] = tuple(_STATEMENTS)

# index key -> baostock constituent query function
_INDEXES: dict[str, str] = {"hs300": "query_hs300_stocks"}

# Deliberately NOT importing pandas: baostock ships it, but pulling it into app
# code would break mypy strict. `ResultData` is iterated row by row instead.


def _to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    parsed = _to_float(value)
    return None if parsed is None else int(parsed)


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    year, month, day = value.split("-")
    return date(int(year), int(month), int(day))


def _board(code: str, symbol: str) -> str:
    exchange = code.split(".", 1)[0]
    if exchange == "bj":
        return "北交所"
    if symbol.startswith(("688", "689")):
        return "科创板"
    if symbol.startswith(("300", "301")):
        return "创业板"
    return "主板"


class BaostockDataSource:
    """`StockDataSource` backed by the baostock SDK.

    Owns the login session (use as a context manager), rate-limits every call
    with `STOCK_SYNC_PACE_SECONDS`, retries transient failures
    `STOCK_SYNC_RETRY` times with backoff, and normalizes baostock's quirks:
    empty strings become None, ratios stay decimals, rows are read by field name.
    """

    def __init__(self) -> None:
        self._logged_in = False

    def __enter__(self) -> Self:
        with contextlib.redirect_stdout(io.StringIO()):
            result = bs.login()
        if result.error_code != "0":
            raise RuntimeError(f"baostock login failed: {result.error_msg}")
        self._logged_in = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._logged_in:
            with contextlib.redirect_stdout(io.StringIO()):
                bs.logout()
            self._logged_in = False

    # ---- internals ---------------------------------------------------------
    def _call(self, fn: Callable[..., Any], **kwargs: Any) -> Any:
        """Invoke a baostock query with pacing + retry/backoff.

        Raises the last error if every attempt fails, so the caller can record
        it on the run without aborting the whole batch.
        """
        last_error: Exception | None = None
        for attempt in range(1, settings.STOCK_SYNC_RETRY + 1):
            time.sleep(settings.STOCK_SYNC_PACE_SECONDS)
            try:
                result = fn(**kwargs)
            except Exception as exc:  # noqa: BLE001 - any SDK failure is retryable
                last_error = exc
            else:
                if getattr(result, "error_code", "0") == "0":
                    return result
                last_error = RuntimeError(
                    f"{getattr(fn, '__name__', 'query')} failed: "
                    f"{getattr(result, 'error_msg', '')}"
                )
            if attempt < settings.STOCK_SYNC_RETRY:
                time.sleep(min(2**attempt * 0.5, 10.0))
        raise RuntimeError(f"baostock call failed after retries: {last_error}")

    @staticmethod
    def _rows(result: Any) -> list[dict[str, str]]:
        fields = list(result.fields)
        rows: list[dict[str, str]] = []
        while result.next():
            rows.append(dict(zip(fields, result.get_row_data(), strict=False)))
        return rows

    def _industry_by_code(self) -> dict[str, str]:
        rows = self._rows(self._call(bs.query_stock_industry))
        return {row["code"]: row["industry"] for row in rows if row.get("industry")}

    # ---- StockDataSource ---------------------------------------------------
    def list_stocks(self) -> Iterator[StockRecord]:
        industry = self._industry_by_code()
        rows = self._rows(self._call(bs.query_stock_basic))
        for row in rows:
            if row.get("type") != "1":  # 1 == stock; skip indices/funds
                continue
            code = row["code"]
            symbol = code.split(".", 1)[1]
            yield StockRecord(
                code=code,
                symbol=symbol,
                exchange=code.split(".", 1)[0].upper(),
                board=_board(code, symbol),
                name=row["code_name"],
                industry=industry.get(code),
                sec_type=_to_int(row.get("type")) or 1,
                status=_to_int(row.get("status")) or 0,
                ipo_date=_to_date(row.get("ipoDate")),
                out_date=_to_date(row.get("outDate")),
            )

    def list_index_members(self, *, index: str, as_of: date) -> Iterator[str]:
        query_name = _INDEXES.get(index)
        if query_name is None:
            raise ValueError(f"unknown index {index!r}; known: {sorted(_INDEXES)}")
        result = self._call(getattr(bs, query_name), date=as_of.isoformat())
        for row in self._rows(result):
            code = row.get("code")
            if code:
                yield code

    def iter_daily_bars(
        self, *, code: str, start: date, end: date
    ) -> Iterator[DailyBarRecord]:
        result = self._call(
            bs.query_history_k_data_plus,
            code=code,
            fields=_K_FIELDS,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency="d",
            adjustflag="3",
        )
        for row in self._rows(result):
            trade_date = _to_date(row.get("date"))
            if trade_date is None:
                continue
            yield DailyBarRecord(
                code=code,
                trade_date=trade_date,
                open=_to_float(row.get("open")),
                high=_to_float(row.get("high")),
                low=_to_float(row.get("low")),
                close=_to_float(row.get("close")),
                preclose=_to_float(row.get("preclose")),
                volume=_to_float(row.get("volume")),
                amount=_to_float(row.get("amount")),
                pct_chg=_to_float(row.get("pctChg")),
                turn=_to_float(row.get("turn")),
                tradestatus=_to_int(row.get("tradestatus")),
                is_st=_to_int(row.get("isST")),
                pe_ttm=_to_float(row.get("peTTM")),
                pb_mrq=_to_float(row.get("pbMRQ")),
                ps_ttm=_to_float(row.get("psTTM")),
                pcf_ncf_ttm=_to_float(row.get("pcfNcfTTM")),
            )

    def query_financial(
        self,
        *,
        code: str,
        year: int,
        quarter: int,
        statements: Sequence[str],
    ) -> FinancialRecord | None:
        metrics: dict[str, float | None] = {}
        stat_date: date | None = None
        pub_date: date | None = None
        for name in statements:
            query_name, mapping = _STATEMENTS[name]
            rows = self._rows(
                self._call(
                    getattr(bs, query_name), code=code, year=year, quarter=quarter
                )
            )
            if not rows:
                continue
            row = rows[0]
            stat_date = stat_date or _to_date(row.get("statDate"))
            pub_date = pub_date or _to_date(row.get("pubDate"))
            for raw_field, column in mapping.items():
                metrics[column] = _to_float(row.get(raw_field))
        if stat_date is None:
            return None
        return FinancialRecord(
            code=code, stat_date=stat_date, pub_date=pub_date, metrics=metrics
        )
