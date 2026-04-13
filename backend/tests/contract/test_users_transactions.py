"""
T039 — Test kontraktowy: GET /api/v1/users/me/transactions

Weryfikuje schemat odpowiedzi, paginację i filtrowanie po typie.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.domain.transactions import finalize_transaction
from src.models.user import User


async def _do_purchase(session: AsyncSession, user: User, amount: float = 50.0) -> None:
    """Pomocnicza: wykonuje pełny zakup."""
    code, _ = await generate_code(session, user)
    token, *_ = await verify_code(session, code, amount, "terminal-dev")
    await finalize_transaction(session, token)
    await session.commit()


@pytest.mark.asyncio
class TestTransactionsContract:
    async def test_success_returns_200(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        assert resp.status_code == 200

    async def test_response_schema_fields(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_empty_history_returns_empty_list(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_transaction_item_schema(
        self,
        authed_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        await _do_purchase(session, user)
        resp = await authed_client.get("/api/v1/users/me/transactions")
        items = resp.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert "id" in item
        assert "type" in item
        assert "gross_amount_pln" in item
        assert "discount_amount_pln" in item
        assert "net_amount_pln" in item
        assert "discount_pct_snapshot" in item
        assert "pos_terminal_id" in item
        assert "created_at" in item

    async def test_pagination_page_size(
        self,
        authed_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        """Domyślny page_size zwraca ≤ zdefiniowaną wartość."""
        await _do_purchase(session, user, 50.0)
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] > 0

    async def test_filter_by_type_zakup(
        self,
        authed_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        """Filtrowanie po type=ZAKUP zwraca tylko zakupy."""
        await _do_purchase(session, user)
        resp = await authed_client.get(
            "/api/v1/users/me/transactions", params={"type": "ZAKUP"}
        )
        data = resp.json()
        for item in data["items"]:
            assert item["type"] == "ZAKUP"

    async def test_no_auth_returns_401(
        self, http_client: AsyncClient
    ):
        resp = await http_client.get("/api/v1/users/me/transactions")
        assert resp.status_code == 401

    async def test_total_count_matches_items(
        self,
        authed_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        await _do_purchase(session, user)
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["total"] >= len(data["items"])
