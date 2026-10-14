"""Stock sync orchestration.

Depends on the `StockDataSource` Protocol, never on a concrete vendor, so tests
inject a fake and stay offline. Owns the transaction boundary: each batch or
per-code unit of work is committed on its own, so a long backfill is resumable
and one bad security never rolls back the rest. Progress is derived from the
data itself (no progress table): daily resumes from `max(trade_date)`, financial
from the periods already stored. Combined with upserts, re-running is safe.
"""

import logging
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

from sqlmodel import Session

from app.datasources.base import FinancialRecord, StockDataSource
from app.models import DailyQuote, FinancialReport, Stock, SyncRun
from app.models.base import get_datetime_utc
from app.repositories import financial as financial_repo
from app.repositories import quote as quote_repo
from app.repositories import stock as stock_repo
from app.repositories import sync as sync_repo
from app.schemas.stock import SyncRunPublic, SyncRunsPublic

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500

# quarter -> (month, day) of its period end
_QUARTER_END: dict[int, tuple[int, int]] = {
    1: (3, 31),
    2: (6, 30),
    3: (9, 30),
    4: (12, 31),
}


def quarter_end(year: int, quarter: int) -> date:
    month, day = _QUARTER_END[quarter]
    return date(year, month, day)


def recent_periods(*, quarters: int, as_of: date) -> list[tuple[int, int]]:
    """The last `quarters` completed report periods, oldest first.

    The current quarter is excluded: its report is not published yet, so only
    periods ending at or before the previous quarter are safe to request.
    """
    quarter = (as_of.month - 1) // 3 + 1
    year = as_of.year
    quarter -= 1
    if quarter == 0:
        quarter, year = 4, year - 1
    periods: list[tuple[int, int]] = []
    for _ in range(quarters):
        periods.append((year, quarter))
        quarter -= 1
        if quarter == 0:
            quarter, year = 4, year - 1
    periods.reverse()
    return periods


def resolve_universe(
    *, session: Session, data_source: StockDataSource, universe: str, as_of: date
) -> list[str]:
    """Expand a universe name into codes: "all" from our table, else an index."""
    if universe == "all":
        return stock_repo.list_all_codes(session=session)
    return list(data_source.list_index_members(index=universe, as_of=as_of))


def _start_run(
    *,
    session: Session,
    dataset: str,
    scope: str,
    params: dict[str, Any] | None,
) -> SyncRun:
    run = SyncRun(dataset=dataset, scope=scope, params=params, status="running")
    sync_repo.add_run(session=session, run=run)
    session.commit()
    session.refresh(run)
    return run


def _finish_run(
    *,
    session: Session,
    run: SyncRun,
    total: int,
    processed: int,
    failed: int,
    last_error: str | None,
) -> SyncRun:
    run.finished_at = get_datetime_utc()
    run.total = total
    run.processed = processed
    run.failed = failed
    run.last_error = last_error
    run.status = "failed" if failed else "success"
    sync_repo.update_run(session=session, run=run)
    session.commit()
    session.refresh(run)
    return run


def sync_stock_list(
    *, session: Session, data_source: StockDataSource, scope: str = "all"
) -> SyncRun:
    run = _start_run(session=session, dataset="stock_list", scope=scope, params=None)
    total = processed = failed = 0
    last_error: str | None = None
    batch: list[Stock] = []
    try:
        for record in data_source.list_stocks():
            total += 1
            batch.append(Stock.model_validate(record, from_attributes=True))
            if len(batch) >= _BATCH_SIZE:
                stock_repo.upsert_stocks(session=session, stocks=batch)
                session.commit()
                processed += len(batch)
                batch.clear()
        if batch:
            stock_repo.upsert_stocks(session=session, stocks=batch)
            session.commit()
            processed += len(batch)
    except Exception as exc:  # noqa: BLE001 - record and keep going
        session.rollback()
        last_error = str(exc)
        failed = total - processed
        logger.exception("sync_stock_list failed")
    return _finish_run(
        session=session,
        run=run,
        total=total,
        processed=processed,
        failed=failed,
        last_error=last_error,
    )


def sync_daily(
    *,
    session: Session,
    data_source: StockDataSource,
    codes: Sequence[str],
    start: date,
    end: date,
    scope: str,
) -> SyncRun:
    run = _start_run(
        session=session,
        dataset="daily",
        scope=scope,
        params={"start": start.isoformat(), "end": end.isoformat()},
    )
    total = len(codes)
    processed = failed = 0
    last_error: str | None = None
    for code in codes:
        last = quote_repo.max_trade_date(session=session, code=code)
        code_start = start if last is None else max(start, last + timedelta(days=1))
        if code_start > end:
            processed += 1
            continue
        try:
            bars = [
                # DailyQuote's field set matches DailyBarRecord's
                DailyQuote.model_validate(bar, from_attributes=True)
                for bar in data_source.iter_daily_bars(
                    code=code, start=code_start, end=end
                )
            ]
            quote_repo.upsert_quotes(session=session, quotes=bars)
            session.commit()
            processed += 1
        except Exception as exc:  # noqa: BLE001 - one code must not kill the run
            session.rollback()
            failed += 1
            last_error = f"{code}: {exc}"
            logger.warning("sync_daily failed for %s: %s", code, exc)
    return _finish_run(
        session=session,
        run=run,
        total=total,
        processed=processed,
        failed=failed,
        last_error=last_error,
    )


def _financial_model(record: FinancialRecord) -> FinancialReport:
    data: dict[str, Any] = {
        "code": record.code,
        "stat_date": record.stat_date,
        "pub_date": record.pub_date,
    }
    data.update(record.metrics)
    return FinancialReport.model_validate(data)


def sync_financial(
    *,
    session: Session,
    data_source: StockDataSource,
    codes: Sequence[str],
    periods: Sequence[tuple[int, int]],
    statements: Sequence[str],
    scope: str,
) -> SyncRun:
    run = _start_run(
        session=session,
        dataset="financial",
        scope=scope,
        params={"periods": list(periods), "statements": list(statements)},
    )
    total = len(codes) * len(periods)
    processed = failed = 0
    last_error: str | None = None
    for code in codes:
        have = financial_repo.existing_stat_dates(session=session, code=code)
        for year, quarter in periods:
            target = quarter_end(year, quarter)
            if target in have:
                processed += 1
                continue
            try:
                record = data_source.query_financial(
                    code=code, year=year, quarter=quarter, statements=statements
                )
                if record is not None:
                    financial_repo.upsert_financials(
                        session=session, reports=[_financial_model(record)]
                    )
                session.commit()
                processed += 1
            except Exception as exc:  # noqa: BLE001 - one period must not kill it
                session.rollback()
                failed += 1
                last_error = f"{code} {year}Q{quarter}: {exc}"
                logger.warning(
                    "sync_financial failed for %s %sQ%s", code, year, quarter
                )
    return _finish_run(
        session=session,
        run=run,
        total=total,
        processed=processed,
        failed=failed,
        last_error=last_error,
    )


def list_sync_runs(*, session: Session, skip: int, limit: int) -> SyncRunsPublic:
    count = sync_repo.count_runs(session=session)
    runs = sync_repo.list_runs(session=session, skip=skip, limit=limit)
    data = [SyncRunPublic.model_validate(run, from_attributes=True) for run in runs]
    return SyncRunsPublic(data=data, count=count)
