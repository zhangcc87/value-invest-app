from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import DailyQuote, FinancialReport, Stock
from app.repositories import financial as financial_repo
from app.repositories import quote as quote_repo
from app.repositories import stock as stock_repo

STOCK_CODE = "sh.API01"


@pytest.fixture(scope="module", autouse=True)
def seeded_stock(db: Session) -> None:
    stock_repo.upsert_stocks(
        session=db,
        stocks=[
            Stock(
                code=STOCK_CODE,
                symbol="API01",
                exchange="SH",
                board="主板",
                name="接口测试股",
                industry="测试行业",
                status=1,
            )
        ],
    )
    quote_repo.upsert_quotes(
        session=db,
        quotes=[
            DailyQuote(code=STOCK_CODE, trade_date=date(2025, 1, 2), close=10.5),
            DailyQuote(code=STOCK_CODE, trade_date=date(2025, 1, 3), close=11.0),
        ],
    )
    financial_repo.upsert_financials(
        session=db,
        reports=[
            FinancialReport(
                code=STOCK_CODE,
                stat_date=date(2024, 12, 31),
                pub_date=date(2025, 3, 30),
                roe_avg=0.25,
            )
        ],
    )
    db.commit()


def test_read_stock_detail(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/{STOCK_CODE}")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == STOCK_CODE
    assert body["name"] == "接口测试股"
    assert body["board"] == "主板"


def test_read_unknown_stock_is_404(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/sh.NOPE")
    assert response.status_code == 404


def test_read_stocks_list_with_filters(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/", params={"q": "API01"})
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["data"][0]["code"] == STOCK_CODE

    matched = client.get(
        f"{settings.API_V1_STR}/stocks/",
        params={"q": "API01", "board": "主板", "status": 1},
    )
    assert matched.json()["count"] == 1

    excluded = client.get(
        f"{settings.API_V1_STR}/stocks/", params={"q": "API01", "status": 0}
    )
    assert excluded.json()["count"] == 0


def test_read_industries(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/industries")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert "测试行业" in body
    assert body == sorted(body)


def test_read_stock_quotes_with_range(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/{STOCK_CODE}/quotes")
    assert response.status_code == 200
    quotes = response.json()
    assert [q["trade_date"] for q in quotes] == ["2025-01-02", "2025-01-03"]

    ranged = client.get(
        f"{settings.API_V1_STR}/stocks/{STOCK_CODE}/quotes",
        params={"start": "2025-01-03"},
    )
    assert [q["trade_date"] for q in ranged.json()] == ["2025-01-03"]


def test_read_stock_financials(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/stocks/{STOCK_CODE}/financials")
    assert response.status_code == 200
    reports = response.json()
    assert len(reports) == 1
    assert reports[0]["stat_date"] == "2024-12-31"
    assert reports[0]["pub_date"] == "2025-03-30"
    assert reports[0]["roe_avg"] == 0.25


def test_sync_runs_requires_superuser(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    unauthorized = client.get(f"{settings.API_V1_STR}/stocks/sync/runs")
    assert unauthorized.status_code == 401

    authorized = client.get(
        f"{settings.API_V1_STR}/stocks/sync/runs", headers=superuser_token_headers
    )
    assert authorized.status_code == 200
    assert "data" in authorized.json()
