"""
T065 — Audit log operacyjny.

Rejestruje zdarzenia:
- generowanie kodów OTP
- próby logowania (sukces / porażka)
- blokady konta

Zapis do tabeli hr_events jest zbyt kosztowny dla logów audytu, dlatego
używamy standardowego mechanizmu Python logging z poziomem AUDIT (25).
W środowisku produkcyjnym logi powinny być kierowane do zewnętrznego systemu
(np. CloudWatch, Datadog, Elasticsearch).
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional


# Poziom AUDIT między INFO (20) a WARNING (30)
AUDIT_LEVEL = 25
logging.addLevelName(AUDIT_LEVEL, "AUDIT")


def _audit(logger: logging.Logger, msg: str, *args: object, **kwargs: object) -> None:
    if logger.isEnabledFor(AUDIT_LEVEL):
        logger.log(AUDIT_LEVEL, msg, *args, **kwargs)


audit_logger = logging.getLogger("bonusapp.audit")


def log_code_generated(
    hr_employee_id: str,
    user_id: uuid.UUID,
    code_id: uuid.UUID,
) -> None:
    """Rejestruje pomyślne wygenerowanie kodu OTP."""
    _audit(
        audit_logger,
        "CODE_GENERATED employee=%s user_id=%s code_id=%s ts=%s",
        hr_employee_id,
        user_id,
        code_id,
        datetime.now(timezone.utc).isoformat(),
    )


def log_login_success(
    hr_employee_id: str,
    user_id: uuid.UUID,
    jti: uuid.UUID,
) -> None:
    """Rejestruje pomyślne zalogowanie."""
    _audit(
        audit_logger,
        "LOGIN_SUCCESS employee=%s user_id=%s jti=%s ts=%s",
        hr_employee_id,
        user_id,
        jti,
        datetime.now(timezone.utc).isoformat(),
    )


def log_login_failure(
    hr_employee_id: str,
    attempt_number: int,
    reason: str,
) -> None:
    """Rejestruje nieudaną próbę logowania."""
    _audit(
        audit_logger,
        "LOGIN_FAILURE employee=%s attempt=%d reason=%s ts=%s",
        hr_employee_id,
        attempt_number,
        reason,
        datetime.now(timezone.utc).isoformat(),
    )


def log_account_locked(
    hr_employee_id: str,
    user_id: uuid.UUID,
    locked_until: datetime,
) -> None:
    """Rejestruje zablokowanie konta po przekroczeniu limitu prób."""
    _audit(
        audit_logger,
        "ACCOUNT_LOCKED employee=%s user_id=%s locked_until=%s ts=%s",
        hr_employee_id,
        user_id,
        locked_until.isoformat(),
        datetime.now(timezone.utc).isoformat(),
    )


def log_pin_changed(
    hr_employee_id: str,
    user_id: uuid.UUID,
    source: Literal["user", "reset", "onboarding"] = "user",
) -> None:
    """Rejestruje zmianę PIN-u (source: 'user' | 'reset' | 'onboarding')."""
    _audit(
        audit_logger,
        "PIN_CHANGED employee=%s user_id=%s source=%s ts=%s",
        hr_employee_id,
        user_id,
        source,
        datetime.now(timezone.utc).isoformat(),
    )
