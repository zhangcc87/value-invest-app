from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, delete

from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from app.models import Item, User
from app.services.seed import init_db
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

assert settings.TEST_DATABASE_URL is not None, (
    "TEST_DATABASE_URL is not set. Add it to the root .env so the test suite runs "
    "against a dedicated database instead of truncating development data."
)
test_engine = create_engine(str(settings.TEST_DATABASE_URL), pool_pre_ping=True)


def _get_test_session() -> Generator[Session]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)
    app.dependency_overrides[get_db] = _get_test_session
    with Session(test_engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
