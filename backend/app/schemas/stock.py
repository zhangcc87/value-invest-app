import uuid
from datetime import date, datetime
from typing import Any

from sqlmodel import Field, SQLModel


# ---- Stock master data -------------------------------------------------------
class StockBase(SQLModel):
    code: str = Field(max_length=16)  # baostock code, e.g. "sh.600519"
    symbol: str = Field(max_length=10)  # bare code, e.g. "600519"
    exchange: str = Field(max_length=4)  # "SH" | "SZ" | "BJ"
    board: str = Field(max_length=16)  # 主板 / 创业板 / 科创板 / 北交所
    name: str = Field(max_length=64)
    industry: str | None = Field(default=None, max_length=64)
    sec_type: int = 1  # baostock type: 1 stock, 2 index, ...
    status: int = 1  # 1 listed, 0 delisted
    ipo_date: date | None = None
    out_date: date | None = None


class StockPublic(StockBase):
    updated_at: datetime | None = None


class StocksPublic(SQLModel):
    data: list[StockPublic]
    count: int


# ---- Daily price + valuation ------------------------------------------------
class DailyQuoteBase(SQLModel):
    code: str = Field(max_length=16)
    trade_date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    preclose: float | None = None
    volume: float | None = None
    amount: float | None = None
    pct_chg: float | None = None  # percent, e.g. 0.5562 = 0.5562%
    turn: float | None = None  # turnover rate, percent
    tradestatus: int | None = None  # 1 trading, 0 suspended
    is_st: int | None = None  # 1 = ST
    pe_ttm: float | None = None
    pb_mrq: float | None = None
    ps_ttm: float | None = None
    pcf_ncf_ttm: float | None = None


class DailyQuotePublic(DailyQuoteBase):
    pass


# ---- Quarterly financials ---------------------------------------------------
# All ratio columns are stored as returned by baostock: DECIMALS, not percents
# (roe_avg=0.3446 means 34.46%).
class FinancialReportBase(SQLModel):
    code: str = Field(max_length=16)
    stat_date: date  # report period end, e.g. 2025-12-31
    pub_date: date | None = None  # announcement date (point-in-time)

    # query_profit_data
    roe_avg: float | None = None
    np_margin: float | None = None
    gp_margin: float | None = None
    net_profit: float | None = None
    eps_ttm: float | None = None
    mb_revenue: float | None = None
    total_share: float | None = None
    liqa_share: float | None = None

    # query_growth_data
    yoy_equity: float | None = None
    yoy_asset: float | None = None
    yoy_ni: float | None = None
    yoy_eps_basic: float | None = None
    yoy_pni: float | None = None

    # query_balance_data
    current_ratio: float | None = None
    quick_ratio: float | None = None
    cash_ratio: float | None = None
    yoy_liability: float | None = None
    liability_to_asset: float | None = None
    asset_to_equity: float | None = None

    # query_cash_flow_data
    cato_asset: float | None = None
    ncato_asset: float | None = None
    tangible_asset_to_asset: float | None = None
    ebit_to_interest: float | None = None
    cfo_to_or: float | None = None
    cfo_to_np: float | None = None
    cfo_to_gr: float | None = None

    # query_operation_data
    nr_turn_ratio: float | None = None
    nr_turn_days: float | None = None
    inv_turn_ratio: float | None = None
    inv_turn_days: float | None = None
    ca_turn_ratio: float | None = None
    asset_turn_ratio: float | None = None

    # query_dupont_data
    dupont_roe: float | None = None
    dupont_asset_sto_equity: float | None = None
    dupont_asset_turn: float | None = None
    dupont_pnitoni: float | None = None
    dupont_nitogr: float | None = None
    dupont_tax_burden: float | None = None
    dupont_intburden: float | None = None
    dupont_ebittogr: float | None = None


class FinancialReportPublic(FinancialReportBase):
    pass


# ---- Sync bookkeeping -------------------------------------------------------
class SyncRunPublic(SQLModel):
    id: uuid.UUID
    dataset: str  # stock_list | daily | financial
    scope: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    status: str  # running | success | failed
    total: int | None = None
    processed: int | None = None
    failed: int | None = None
    last_error: str | None = None
    params: dict[str, Any] | None = None


class SyncRunsPublic(SQLModel):
    data: list[SyncRunPublic]
    count: int
