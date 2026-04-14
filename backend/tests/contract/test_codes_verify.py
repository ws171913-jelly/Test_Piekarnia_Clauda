"""
T023 — Test kontraktowy: POST /api/v1/codes/verify

Weryfikuje:
- schemat odpowiedzi przy sukcesie (200)
- błąd dla wygasłego / nieprawidłowego kodu (422)
- wymaganie klucza POS (401)
"""
import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
class TestVerifyCodeContract:
    async def _generate(self, authed_client: AsyncClient) -> str:
        """Pomocnicza: generuje kod OTP przez HTTP API i zwraca plaintext kodu."""
        resp = await authed_client.post("/api/v1/codes")
        assert resp.status_code == 201
        return resp.json()["code"]

    async def test_success_returns_200(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
        user: User,
    ):
        code = await self._generate(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": code, "gross_amount_pln": 100.0},
        )
        assert resp.status_code == 200

    async def test_response_schema(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
        user: User,
    ):
        code = await self._generate(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": code, "gross_amount_pln": 100.0},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "verification_token" in data
        assert "discount_amount_pln" in data
        assert "discount_pct" in data
        assert "net_amount_pln" in data
        assert "code_id" in data

    async def test_discount_amount_correct(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
        user: User,
    ):
        """Koszyk testowy = 20%, kwota = 100 PLN → rabat = 20 PLN."""
        code = await self._generate(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": code, "gross_amount_pln": 100.0},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["discount_pct"] == 20.0
        assert data["discount_amount_pln"] == 20.0
        assert data["net_amount_pln"] == 80.0

    async def test_invalid_code_returns_422(
        self, pos_client: AsyncClient
    ):
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": "000000", "gross_amount_pln": 100.0},
        )
        assert resp.status_code == 422

    async def test_no_pos_key_returns_401(
        self, http_client: AsyncClient
    ):
        resp = await http_client.post(
            "/api/v1/codes/verify",
            json={"code": "123456", "gross_amount_pln": 100.0},
        )
        assert resp.status_code == 401

    async def test_zero_gross_returns_422(
        self, pos_client: AsyncClient
    ):
        """Kwota brutto musi być > 0."""
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": "123456", "gross_amount_pln": 0.0},
        )
        assert resp.status_code == 422

    async def test_negative_gross_returns_422(
        self, pos_client: AsyncClient
    ):
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": "123456", "gross_amount_pln": -50.0},
        )
        assert resp.status_code == 422

    async def test_verification_token_is_string(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
        user: User,
    ):
        code = await self._generate(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/verify",
            json={"code": code, "gross_amount_pln": 100.0},
        )
        data = resp.json()
        assert isinstance(data["verification_token"], str)
        assert len(data["verification_token"]) > 20
