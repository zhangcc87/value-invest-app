from dataclasses import replace
from datetime import date

from sqlmodel import Session, col, func, select

from app.datasources.baostock import _STATEMENTS
from app.models import DailyQuote, FinancialReport, Stock
from app.repositories import stock as stock_repo
from app.services import sync
from tests.utils.fake_datasource import FakeDataSource, default_stocks


def _count(db: Session, model: type, code: str) -> int:
    statement = select(func.count()).select_from(model).where(col(model.code) == code)
    return db.exec(statement).one()


def _seed_stock(db: Session, code: str) -> None:
    stock_repo.upsert_stocks(
        session=db,
        stocks=[
            Stock(
                code=code,
                symbol=code.split(".", 1)[1],
                exchange=code.split(".", 1)[0].upper(),
                board="主板",
                name="测试",
            )
        ],
    )
    db.commit()


def test_sync_stock_list_upserts_and_refreshes(db: Session) -> None:
    run = sync.sync_stock_list(session=db, data_source=FakeDataSource())
    assert (run.status, run.total, run.processed, run.failed) == ("success", 2, 2, 0)

    changed = default_stocks()
    changed[0] = replace(changed[0], name="贵州茅台改")
    sync.sync_stock_list(session=db, data_source=FakeDataSource(stocks=changed))

    db.expire_all()
    assert _count(db, Stock, "sh.600519") == 1  # upsert, not duplicate
    stock = db.get(Stock, "sh.600519")
    assert stock is not None
    assert stock.name == "贵州茅台改"
    assert stock.exchange == "SH" and stock.board == "主板"


def test_sync_daily_resumes_from_last_stored_bar(db: Session) -> None:
    _seed_stock(db, "sh.T0001")
    run = sync.sync_daily(
        session=db,
        data_source=FakeDataSource(),
        codes=["sh.T0001"],
        start=date(2025, 1, 1),
        end=date(2025, 1, 5),
        scope="codes",
    )
    assert run.status == "success" and run.processed == 1
    assert _count(db, DailyQuote, "sh.T0001") == 5

    # Same range again: already current, so nothing is fetched.
    fake = FakeDataSource()
    sync.sync_daily(
        session=db,
        data_source=fake,
        codes=["sh.T0001"],
        start=date(2025, 1, 1),
        end=date(2025, 1, 5),
        scope="codes",
    )
    assert fake.daily_requests == []
    assert _count(db, DailyQuote, "sh.T0001") == 5

    # Extended range: only the two new days are requested and appended.
    fake = FakeDataSource()
    sync.sync_daily(
        session=db,
        data_source=fake,
        codes=["sh.T0001"],
        start=date(2025, 1, 1),
        end=date(2025, 1, 7),
        scope="codes",
    )
    assert fake.daily_requests == [("sh.T0001", date(2025, 1, 6), date(2025, 1, 7))]
    assert _count(db, DailyQuote, "sh.T0001") == 7


def test_sync_daily_records_per_code_failure(db: Session) -> None:
    _seed_stock(db, "sh.T0002")
    run = sync.sync_daily(
        session=db,
        data_source=FakeDataSource(fail_codes=frozenset({"sh.T0002"})),
        codes=["sh.T0002"],
        start=date(2025, 1, 1),
        end=date(2025, 1, 3),
        scope="codes",
    )
    assert run.status == "failed"
    assert run.failed == 1 and run.processed == 0
    assert run.last_error is not None and "sh.T0002" in run.last_error


def test_sync_daily_requires_stock_row_first(db: Session) -> None:
    # dailyquote.code has an FK to stock.code, so an unknown code fails loudly.
    run = sync.sync_daily(
        session=db,
        data_source=FakeDataSource(),
        codes=["sh.MISSING"],
        start=date(2025, 1, 1),
        end=date(2025, 1, 2),
        scope="codes",
    )
    assert run.status == "failed" and run.failed == 1


def test_sync_financial_merges_requested_statements(db: Session) -> None:
    _seed_stock(db, "sh.T0003")
    run = sync.sync_financial(
        session=db,
        data_source=FakeDataSource(),
        codes=["sh.T0003"],
        periods=[(2024, 3), (2024, 4)],
        statements=["profit", "balance"],
        scope="codes",
    )
    assert run.status == "success" and run.total == 2 and run.processed == 2

    db.expire_all()
    report = db.get(FinancialReport, ("sh.T0003", date(2024, 12, 31)))
    assert report is not None
    assert report.pub_date == date(2025, 1, 30)
    assert report.roe_avg == 0.5 and report.current_ratio == 0.5  # profit + balance
    assert report.yoy_ni is None  # growth was not requested
    assert _count(db, FinancialReport, "sh.T0003") == 2


def test_sync_financial_skips_stored_periods(db: Session) -> None:
    _seed_stock(db, "sh.T0004")
    sync.sync_financial(
        session=db,
        data_source=FakeDataSource(),
        codes=["sh.T0004"],
        periods=[(2024, 4)],
        statements=["profit"],
        scope="codes",
    )
    fake = FakeDataSource()
    run = sync.sync_financial(
        session=db,
        data_source=fake,
        codes=["sh.T0004"],
        periods=[(2024, 4)],
        statements=["profit"],
        scope="codes",
    )
    assert fake.financial_requests == []
    assert run.processed == 1 and run.failed == 0


def test_sync_financial_skips_unpublished_periods(db: Session) -> None:
    _seed_stock(db, "sh.T0005")
    sync.sync_financial(
        session=db,
        data_source=FakeDataSource(periods_with_data={(2024, 4)}),
        codes=["sh.T0005"],
        periods=[(2024, 3), (2024, 4)],
        statements=["profit"],
        scope="codes",
    )
    db.expire_all()
    assert _count(db, FinancialReport, "sh.T0005") == 1


def test_recent_periods_excludes_current_quarter() -> None:
    # Q3-2026 ends 2026-09-30 but is not published by mid-October.
    assert sync.recent_periods(quarters=3, as_of=date(2026, 10, 13)) == [
        (2026, 1),
        (2026, 2),
        (2026, 3),
    ]
    assert sync.recent_periods(quarters=2, as_of=date(2026, 1, 5)) == [
        (2025, 3),
        (2025, 4),
    ]


def test_resolve_universe_from_table_and_index(db: Session) -> None:
    sync.sync_stock_list(session=db, data_source=FakeDataSource())
    universe = sync.resolve_universe(
        session=db, data_source=FakeDataSource(), universe="all", as_of=date(2026, 1, 1)
    )
    assert "sh.600519" in universe
    index = sync.resolve_universe(
        session=db,
        data_source=FakeDataSource(members=["sh.600519"]),
        universe="hs300",
        as_of=date(2026, 1, 1),
    )
    assert index == ["sh.600519"]


def test_adapter_statement_columns_exist_on_model() -> None:
    # Guards the vendor->column mapping against silent drift.
    columns = set(FinancialReport.model_fields)
    for name, (_, mapping) in _STATEMENTS.items():
        assert set(mapping.values()) <= columns, name
