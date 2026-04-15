import hashlib
import hmac
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request, status

from src.api.deps import DBSession
from src.config import settings
from src.domain import hr_processor
from src.models.hr_event import HrEvent, HrEventStatus
from src.schemas.hr_events import HrEventRequest, HrEventResponse

router = APIRouter()


async def _verify_hmac(request: Request, signature_header: str | None) -> None:
    """Weryfikuje podpis HMAC-SHA256 z nagłówka X-Hub-Signature-256."""
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak nagłówka X-Hub-Signature-256",
        )

    body = await request.body()
    expected = hmac.new(
        settings.hmac_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    expected_header = f"sha256={expected}"

    if not hmac.compare_digest(expected_header, signature_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy podpis HMAC",
        )


@router.post("", response_model=HrEventResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_hr_event(
    request: Request,
    body: HrEventRequest,
    session: DBSession,
    x_hub_signature_256: str | None = Header(default=None),
) -> HrEventResponse:
    """Odbiera i przetwarza zdarzenie HR po weryfikacji podpisu HMAC-SHA256."""
    await _verify_hmac(request, x_hub_signature_256)

    event_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    hr_event = HrEvent(
        id=event_id,
        event_type=body.event_type,
        payload=body.payload.model_dump(mode="json"),
        status=HrEventStatus.OCZEKUJACE,
        received_at=now,
    )
    session.add(hr_event)
    await session.flush()

    try:
        temp_pin = await hr_processor.process_hr_event(
            session, body.event_type, body.payload, event_id
        )
        hr_event.status = HrEventStatus.PRZETWORZONE
        hr_event.processed_at = datetime.now(timezone.utc)
        await session.commit()
    except (ValueError, LookupError) as exc:
        hr_event.status = HrEventStatus.BLAD
        hr_event.error_message = str(exc)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return HrEventResponse(
        event_id=event_id,
        status=HrEventStatus.PRZETWORZONE,
        temp_pin=temp_pin,
    )
