import uuid

from sqlmodel import Session, col, func, select

from app.models import SyncRun


def add_run(*, session: Session, run: SyncRun) -> SyncRun:
    session.add(run)
    session.flush()
    return run


def update_run(*, session: Session, run: SyncRun) -> SyncRun:
    session.add(run)
    session.flush()
    return run


def get_run(*, session: Session, run_id: uuid.UUID) -> SyncRun | None:
    return session.get(SyncRun, run_id)


def list_runs(*, session: Session, skip: int, limit: int) -> list[SyncRun]:
    statement = (
        select(SyncRun)
        .order_by(col(SyncRun.started_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_runs(*, session: Session) -> int:
    return session.exec(select(func.count()).select_from(SyncRun)).one()
