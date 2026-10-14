"""CLI to sync A-share data from baostock into Postgres.

Trigger this from cron; there is no in-app scheduler. Typical nightly run:

    python app/sync_data.py all                     # every command below
    python app/sync_data.py stocks                  # master data + industry
    python app/sync_data.py daily --universe hs300  # a few minutes
    python app/sync_data.py financial --quarters 4 --statements profit,growth,balance

A full-market 3-year backfill is an overnight job (see backend/README.md).
"""

import argparse
import logging
from datetime import date, timedelta

from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.datasources import BaostockDataSource
from app.datasources.baostock import STATEMENTS
from app.models import SyncRun
from app.services import sync

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# The three cheapest statements (~19万 requests over a 12-quarter full-market
# backfill). Enable cashflow/operation/dupont explicitly when needed.
DEFAULT_STATEMENTS = ("profit", "growth", "balance")
DEFAULT_BACKFILL_DAYS = 365 * 3


def _log_run(run: SyncRun) -> None:
    logger.info(
        "run %s %s: status=%s total=%s processed=%s failed=%s%s",
        run.id,
        run.dataset,
        run.status,
        run.total,
        run.processed,
        run.failed,
        f" last_error={run.last_error}" if run.last_error else "",
    )


def _resolve_codes(
    args: argparse.Namespace, session: Session, data_source: BaostockDataSource
) -> list[str]:
    if args.codes:
        return [code.strip() for code in args.codes.split(",") if code.strip()]
    return sync.resolve_universe(
        session=session,
        data_source=data_source,
        universe=args.universe,
        as_of=date.today(),
    )


def _run_stocks(session: Session, data_source: BaostockDataSource) -> None:
    _log_run(sync.sync_stock_list(session=session, data_source=data_source))


def _run_daily(
    args: argparse.Namespace, session: Session, data_source: BaostockDataSource
) -> None:
    end = date.fromisoformat(args.end) if args.end else date.today()
    start = (
        date.fromisoformat(args.start)
        if args.start
        else end - timedelta(days=DEFAULT_BACKFILL_DAYS)
    )
    codes = _resolve_codes(args, session, data_source)
    if not codes:
        logger.warning("no codes resolved; run `stocks` first or pass --codes")
        return
    logger.info("daily sync: %s codes, %s..%s", len(codes), start, end)
    _log_run(
        sync.sync_daily(
            session=session,
            data_source=data_source,
            codes=codes,
            start=start,
            end=end,
            scope="codes" if args.codes else args.universe,
        )
    )


def _run_financial(
    args: argparse.Namespace, session: Session, data_source: BaostockDataSource
) -> None:
    quarters = (
        args.quarters
        if args.quarters is not None
        else settings.STOCK_SYNC_BACKFILL_QUARTERS
    )
    statements = (
        tuple(part.strip() for part in args.statements.split(",") if part.strip())
        if args.statements
        else DEFAULT_STATEMENTS
    )
    unknown = [name for name in statements if name not in STATEMENTS]
    if unknown:
        raise SystemExit(
            f"unknown statements {unknown}; choose from {list(STATEMENTS)}"
        )
    periods = sync.recent_periods(quarters=quarters, as_of=date.today())
    codes = _resolve_codes(args, session, data_source)
    if not codes:
        logger.warning("no codes resolved; run `stocks` first or pass --codes")
        return
    logger.info(
        "financial sync: %s codes x %s periods, statements=%s",
        len(codes),
        len(periods),
        ",".join(statements),
    )
    _log_run(
        sync.sync_financial(
            session=session,
            data_source=data_source,
            codes=codes,
            periods=periods,
            statements=statements,
            scope="codes" if args.codes else args.universe,
        )
    )


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pace", type=float, default=None, help="seconds between upstream requests"
    )
    parser.add_argument(
        "--retry", type=int, default=None, help="retries per upstream request"
    )


def _add_scope(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--universe", default="all", choices=["all", "hs300"], help="stock universe"
    )
    parser.add_argument(
        "--codes", default=None, help="comma-separated codes; overrides --universe"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sync_data",
        description="Sync A-share data from baostock into Postgres.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    stocks = sub.add_parser("stocks", help="master data + industry")
    _add_common(stocks)

    daily = sub.add_parser("daily", help="daily price + valuation")
    _add_common(daily)
    _add_scope(daily)
    daily.add_argument("--start", default=None, help="YYYY-MM-DD (default: 3y ago)")
    daily.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")

    financial = sub.add_parser("financial", help="quarterly financials")
    _add_common(financial)
    _add_scope(financial)
    financial.add_argument(
        "--quarters", type=int, default=None, help="backfill depth (default: config)"
    )
    financial.add_argument(
        "--statements",
        default=None,
        help=f"comma-separated, from {list(STATEMENTS)} (default: {','.join(DEFAULT_STATEMENTS)})",
    )

    all_cmd = sub.add_parser("all", help="stocks, then daily, then financial")
    _add_common(all_cmd)
    _add_scope(all_cmd)
    all_cmd.add_argument("--start", default=None)
    all_cmd.add_argument("--end", default=None)
    all_cmd.add_argument("--quarters", type=int, default=None)
    all_cmd.add_argument("--statements", default=None)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.pace is not None:
        settings.STOCK_SYNC_PACE_SECONDS = args.pace
    if args.retry is not None:
        settings.STOCK_SYNC_RETRY = args.retry

    with Session(engine) as session, BaostockDataSource() as data_source:
        if args.command in ("stocks", "all"):
            _run_stocks(session, data_source)
        if args.command in ("daily", "all"):
            _run_daily(args, session, data_source)
        if args.command in ("financial", "all"):
            _run_financial(args, session, data_source)


if __name__ == "__main__":
    main()
