from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DBSession
from src.domain import auth as auth_domain
from src.schemas.auth import ChangePinRequest, ChangePinResponse, LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, session: DBSession) -> LoginResponse:
    """
    Logowanie pracownika — numer pracownika + PIN.

    Gdy `must_change_pin=true` w odpowiedzi, klient MUSI wywołać `/auth/change-pin`
    przed uzyskaniem dostępu do innych endpointów.
    """
    try:
        user, token = await auth_domain.authenticate_user(session, body.hr_employee_id, body.pin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return LoginResponse(
        access_token=token,
        must_change_pin=user.must_change_pin,
    )


@router.post("/change-pin", response_model=ChangePinResponse)
async def change_pin(
    body: ChangePinRequest,
    current_user: CurrentUser,
    session: DBSession,
) -> ChangePinResponse:
    """Zmiana PIN-u — wymagana gdy must_change_pin=true lub na żądanie użytkownika."""
    try:
        new_token = await auth_domain.change_pin(
            session, current_user, body.new_pin, body.confirm_pin
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return ChangePinResponse(access_token=new_token)
