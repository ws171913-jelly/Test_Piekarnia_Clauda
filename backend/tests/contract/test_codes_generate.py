"""
T022 — Test kontraktowy: POST /api/v1/codes

Weryfikuje:
- schemat odpowiedzi przy sukcesie (201)
- blokadę karencji (422)
- blokadę zerowego salda (422)
- wymaganie autoryzacji Bearer (401)
"""
from datetime import datetime, timedelta, timezone

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


@pytest.mark.asyncio
class TestGenerateCodeContract:
    async def test_success_returns_201(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.post("/api/v1/codes")
        assert resp.status_code == 201

    async def test_response_schema(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.post("/api/v1/codes")
        assert resp.status_code == 201
        data = resp.json()
        assert "code" in data
        assert "expires_at" in data
        assert "code_id" in data

    async def test_code_is_6_digits(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.post("/api/v1/codes")
        data = resp.json()
        code = data["code"]
        assert len(code) == 6
        assert code.isdigit()

    async def test_code_id_is_uuid(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.post("/api/v1/codes")
        data = resp.json()
        # Nie rzuca wyjątku jeśli to prawidłowy UUID
        uuid.UUID(data["code_id"])

    async def test_no_auth_returns_401(
        self, http_client: AsyncClient
    ):
        resp = await http_client.post("/api/v1/codes")
        assert resp.status_code == 401

    async def test_zero_balance_returns_422(
        self,
        authed_client: AsyncClient,
        _setup_session: AsyncSession,
        user: User,
    ):
        user.current_balance = 0
        await _setup_session.commit()
        resp = await authed_client.post("/api/v1/codes")
        assert resp.status_code == 422
        assert "sald" in resp.json()["detail"].lower()

    async def test_cooldown_returns_422(
        self,
        authed_client: AsyncClient,
        _setup_session: AsyncSession,
        user: User,
    ):
        # Symuluj niedawno wygenerowany kod
        user.last_code_generated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await _setup_session.commit()

        resp = await authed_client.post("/api/v1/codes")
        assert resp.status_code == 422
        assert "karencja" in resp.json()["detail"].lower()

    async def test_expires_at_is_datetime(
        self, authed_client: AsyncClient, user: User
    ):
        resp = await authed_client.post("/api/v1/codes")
        data = resp.json()
        # Parsowalne jako datetime ISO
        dt = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        assert dt > datetime.now(dt.tzinfo)
