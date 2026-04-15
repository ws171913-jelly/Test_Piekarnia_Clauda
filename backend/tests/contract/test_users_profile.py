"""
T038 — Test kontraktowy: GET /api/v1/users/me

Weryfikuje schemat odpowiedzi profilu pracownika i wymagane pola.
"""
import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
class TestUsersProfileContract:
    async def test_success_returns_200(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        assert resp.status_code == 200

    async def test_response_schema_fields(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        data = resp.json()
        assert "hr_employee_id" in data
        assert "current_balance" in data
        assert "balance_expiry_date" in data
        assert "basket" in data
        assert "location_id" in data
        assert "must_change_pin" in data

    async def test_basket_schema_fields(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        basket = resp.json()["basket"]
        assert "id" in basket
        assert "name" in basket
        assert "discount_pct" in basket
        assert "monthly_limit_pln" in basket

    async def test_hr_employee_id_matches(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        assert resp.json()["hr_employee_id"] == user.hr_employee_id

    async def test_balance_is_numeric(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        balance = resp.json()["current_balance"]
        assert isinstance(balance, (int, float))
        assert balance >= 0

    async def test_discount_pct_is_valid_percentage(
        self, authed_client: AsyncClient, user: User
    ):
        """discount_pct mieści się w zakresie 0-100."""
        resp = await authed_client.get("/api/v1/users/me")
        discount_pct = resp.json()["basket"]["discount_pct"]
        assert 0 <= discount_pct <= 100

    async def test_no_auth_returns_401(
        self, http_client: AsyncClient
    ):
        resp = await http_client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_must_change_pin_is_bool(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.get("/api/v1/users/me")
        assert isinstance(resp.json()["must_change_pin"], bool)

    async def test_balance_expiry_date_is_date(
        self, authed_client: AsyncClient, user: User
    ):
        from datetime import date
        resp = await authed_client.get("/api/v1/users/me")
        date_str = resp.json()["balance_expiry_date"]
        parsed_date = date.fromisoformat(date_str)
        assert isinstance(parsed_date, date)
