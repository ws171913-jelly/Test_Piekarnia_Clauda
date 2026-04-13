"""
T024 — Test kontraktowy: POST /api/v1/codes/finalize

Weryfikuje:
- schemat odpowiedzi przy sukcesie (200)
- idempotencję (drugi finalize → 422)
- nieważny token weryfikacji (422)
- aktualizację salda w odpowiedzi
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.codes import generate_code, verify_code
from src.models.user import User


@pytest.mark.asyncio
class TestFinalizeCodeContract:
    async def _generate_and_verify(
        self,
        session: AsyncSession,
        user: User,
        gross_amount: float = 100.0,
    ) -> str:
        """Pomocnicza: generuje OTP i weryfikuje — zwraca verification_token."""
        code, _ = await generate_code(session, user)
        token, _, _, _, _ = await verify_code(
            session, code, gross_amount, "terminal-dev"
        )
        await session.commit()
        return token

    async def test_success_returns_200(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        token = await self._generate_and_verify(session, user)
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert resp.status_code == 200

    async def test_response_schema(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        token = await self._generate_and_verify(session, user)
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        assert "transaction_id" in data
        assert "balance_after_pln" in data
        assert "discount_amount_pln" in data

    async def test_balance_reduced_after_finalize(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        """Saldo po finalizacji = saldo przed - rabat."""
        balance_before = float(user.current_balance)
        token = await self._generate_and_verify(session, user, gross_amount=100.0)
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        expected_balance = balance_before - data["discount_amount_pln"]
        assert abs(data["balance_after_pln"] - expected_balance) < 0.01

    async def test_discount_amount_is_20_pct(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        """Koszyk testowy = 20% → rabat od 100 PLN = 20 PLN."""
        token = await self._generate_and_verify(session, user, gross_amount=100.0)
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        assert data["discount_amount_pln"] == 20.0

    async def test_idempotence_second_finalize_returns_422(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        """Drugi finalize tego samego tokenu → 422."""
        token = await self._generate_and_verify(session, user)
        # Pierwszy finalize — sukces
        r1 = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert r1.status_code == 200

        # Drugi finalize — błąd
        r2 = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        assert r2.status_code == 422

    async def test_invalid_token_returns_422(
        self, http_client: AsyncClient
    ):
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": "nie.prawidlowy.token"},
        )
        assert resp.status_code == 422

    async def test_transaction_id_is_uuid(
        self,
        http_client: AsyncClient,
        session: AsyncSession,
        user: User,
    ):
        token = await self._generate_and_verify(session, user)
        resp = await http_client.post(
            "/api/v1/codes/finalize",
            json={"verification_token": token},
        )
        data = resp.json()
        uuid.UUID(data["transaction_id"])  # nie rzuca jeśli poprawny UUID
