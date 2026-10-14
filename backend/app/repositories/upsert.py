from collections.abc import Sequence
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session, SQLModel


def bulk_upsert(
    *,
    session: Session,
    model: type[SQLModel],
    rows: Sequence[dict[str, Any]],
    conflict_columns: Sequence[str],
) -> None:
    """Idempotent bulk insert: `INSERT ... ON CONFLICT (cols) DO UPDATE`.

    `rows` are plain dicts (one per instance, via `.model_dump()`). Every
    non-conflict column is refreshed on collision, so re-running a sync over an
    overlapping range is safe. Never commits — the service owns the transaction.
    """
    if not rows:
        return
    statement = pg_insert(model).values(list(rows))
    update_columns = {
        column: getattr(statement.excluded, column)
        for column in rows[0]
        if column not in conflict_columns
    }
    statement = statement.on_conflict_do_update(
        index_elements=list(conflict_columns), set_=update_columns
    )
    # Bulk DML: skip ORM identity-map synchronization (it would force a
    # round-trip on ON CONFLICT). Callers commit, which expires stale objects.
    session.exec(statement.execution_options(synchronize_session=False))
