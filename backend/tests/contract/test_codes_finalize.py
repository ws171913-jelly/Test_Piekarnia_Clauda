"""
T024 — Test kontraktowy: POST /api/v1/codes/finalize

Weryfikuje:
- schemat odpowiedzi przy sukcesie (200)
- idempotencję (drugi finalize → 422)
- nieważny token weryfikacji (422)
- aktualizację salda w odpowiedzi

Przepływ HTTP: generate → verify → finalize
(bez bezpośrednich wywołań domeny, żeby uniknąć problemu z event loop asyncpg)
"""
import uuid

import pytest
from httpx import AsyncClient

_POS_KEY = "pos-key-terminal-dev"


@pytest.mark.asyncio
class TestFinalizeCodeContract:
    async def _generate_and_verify(
        self,
        authed_client: AsyncClient,
        gross_amount: float = 100.0,
    ) -> str:
        """Pomocnicza: generuje OTP przez HTTP i weryfikuje — zwraca verification_token."""
        gen_resp = await authed_client.post("/api/v1/codes")
        assert gen_resp.status_code == 201, gen_resp.text
        code = gen_resp.json()["code"]

        verify_resp = await authed_client.post(
            "/api/v1/codes/verify",
            headers={"X-POS-API-Key": _POS_KEY},
            json={"code": code, "gross_amount_pln": gross_amount},
        )
        assert verify_resp.status_code == 200, verify_resp.text
        return verify_resp.json()["verification_token"]

    async def test_success_returns_200(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        token = await self._generate_and_verify(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert resp.status_code == 200

    async def test_response_schema(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        token = await self._generate_and_verify(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        assert "transaction_id" in data
        assert "balance_after_pln" in data
        assert "discount_amount_pln" in data

    async def test_balance_reduced_after_finalize(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        """Saldo po finalizacji = saldo przed - rabat."""
        me_resp = await authed_client.get("/api/v1/users/me")
        assert me_resp.status_code == 200, me_resp.text
        balance_before = me_resp.json()["current_balance"]

        token = await self._generate_and_verify(authed_client, gross_amount=100.0)
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        expected_balance = balance_before - data["discount_amount_pln"]
        assert abs(data["balance_after_pln"] - expected_balance) < 0.01

    async def test_discount_amount_is_20_pct(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        """Koszyk testowy = 20% → rabat od 100 PLN = 20 PLN."""
        token = await self._generate_and_verify(authed_client, gross_amount=100.0)
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        assert data["discount_amount_pln"] == 20.0

    async def test_idempotence_second_finalize_returns_422(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        """Drugi finalize tego samego tokenu → 422."""
        token = await self._generate_and_verify(authed_client)
        # Pierwszy finalize — sukces
        r1 = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert r1.status_code == 200

        # Drugi finalize — błąd
        r2 = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert r2.status_code == 422

    async def test_invalid_token_returns_422(
        self, pos_client: AsyncClient
    ):
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": "nie.prawidlowy.token"},
        )
        assert resp.status_code == 422

    async def test_transaction_id_is_uuid(
        self,
        authed_client: AsyncClient,
        pos_client: AsyncClient,
    ):
        token = await self._generate_and_verify(authed_client)
        resp = await pos_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        uuid.UUID(data["transaction_id"])  # nie rzuca jeśli poprawny UUID
