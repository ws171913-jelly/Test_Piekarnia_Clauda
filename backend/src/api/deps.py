import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_session
from src.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Walidacja JWT Bearer + sprawdzenie JTI względem bazy."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy lub wygasły token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if user_id is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Walidacja JTI — token z nieaktualnym JTI jest odrzucany
    if user.current_jti is None or str(user.current_jti) != jti:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto jest dezaktywowane",
        )

    return user


async def get_pos_terminal_id(
    x_pos_api_key: Annotated[str | None, Header(alias="X-POS-API-Key")] = None,
) -> str:
    """Walidacja klucza API terminala POS."""
    if x_pos_api_key is None or x_pos_api_key not in settings.pos_api_keys_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieznany klucz API terminala POS",
        )
    # W produkcji pobierz terminal_id z bazy na podstawie klucza.
    # Tu generujemy unikalny identyfikator z pełnego hasha API key,
    # aby uniknąć kolizji przy różnych kluczach z tym samym suffixem.
    import hashlib

    key_hash = hashlib.sha256(x_pos_api_key.encode()).hexdigest()[:8]
    return f"terminal-{key_hash}"


CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_session)]
PosTerminalId = Annotated[str, Depends(get_pos_terminal_id)]
