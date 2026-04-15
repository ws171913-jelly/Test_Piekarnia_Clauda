"""
T039 — Test kontraktowy: GET /api/v1/users/me/transactions

Weryfikuje schemat odpowiedzi, paginację i filtrowanie po typie.

Przepływ: generate → verify → finalize → transactions (HTTP only,
bez bezpośrednich wywołań domeny, żeby uniknąć konfliktów blokad
na współdzielonej sesji asyncpg).
"""
import uuid

import pytest
from httpx import AsyncClient

_POS_KEY = "pos-key-terminal-dev"

_POS_HEADERS = {"X-POS-API-Key": _POS_KEY}


async def _do_purchase(authed_client: AsyncClient, gross_amount: float = 50.0) -> None:
    """Pomocnicza: wykonuje pełny zakup przez HTTP."""
    gen_resp = await authed_client.post("/api/v1/codes")
    assert gen_resp.status_code == 201, gen_resp.text
    code = gen_resp.json()["code"]

    verify_resp = await authed_client.post(
        "/api/v1/codes/verify",
        headers=_POS_HEADERS,
        json={"code": code, "gross_amount_pln": gross_amount},
    )
    assert verify_resp.status_code == 200, verify_resp.text
    token = verify_resp.json()["verification_token"]

    fin_resp = await authed_client.post(
        "/api/v1/codes/finalize",
        headers=_POS_HEADERS,
        json={"verification_token": token},
    )
    assert fin_resp.status_code == 200, fin_resp.text


@pytest.mark.asyncio
class TestTransactionsContract:
    async def test_success_returns_200(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        assert resp.status_code == 200

    async def test_response_schema_fields(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_empty_history_returns_empty_list(
        self, authed_client: AsyncClient
    ):
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_transaction_item_schema(
        self, authed_client: AsyncClient
    ):
        await _do_purchase(authed_client)
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
        self, authed_client: AsyncClient
    ):
        """Domyślny page_size zwraca ≤ zdefiniowaną wartość."""
        await _do_purchase(authed_client, 50.0)
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] > 0

    async def test_filter_by_type_zakup(
        self, authed_client: AsyncClient
    ):
        """Filtrowanie po type=ZAKUP zwraca tylko zakupy — przy obecności obu typów."""
        await _do_purchase(authed_client)

        purchase_resp = await authed_client.get("/api/v1/users/me/transactions")
        purchase_id = purchase_resp.json()["items"][0]["id"]

        refund_resp = await authed_client.post(
            "/api/v1/codes/refund",
            headers=_POS_HEADERS,
            json={"original_transaction_id": purchase_id},
        )
        assert refund_resp.status_code == 200, refund_resp.text

        resp = await authed_client.get(
            "/api/v1/users/me/transactions", params={"type": "ZAKUP"}
        )
        data = resp.json()
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["type"] == "ZAKUP"

    async def test_no_auth_returns_401(
        self, http_client: AsyncClient
    ):
        resp = await http_client.get("/api/v1/users/me/transactions")
        assert resp.status_code == 401

    async def test_total_count_matches_items(
        self, authed_client: AsyncClient
    ):
        await _do_purchase(authed_client)
        resp = await authed_client.get("/api/v1/users/me/transactions")
        data = resp.json()
        assert data["total"] >= len(data["items"])
