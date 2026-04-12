from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DBSession, PosTerminalId
from src.domain import codes as codes_domain
from src.domain import transactions as tx_domain
from src.schemas.codes import (
    FinalizeCodeRequest,
    FinalizeCodeResponse,
    GenerateCodeResponse,
    RefundRequest,
    RefundResponse,
    VerifyCodeRequest,
    VerifyCodeResponse,
)

router = APIRouter()


@router.post("", response_model=GenerateCodeResponse, status_code=status.HTTP_201_CREATED)
async def generate_code(current_user: CurrentUser, session: DBSession) -> GenerateCodeResponse:
    """Generuje jednorazowy 6-cyfrowy kod OTP dla zalogowanego pracownika."""
    try:
        code, auth_code = await codes_domain.generate_code(session, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return GenerateCodeResponse(
        code=code,
        expires_at=auth_code.expires_at,
        code_id=auth_code.id,
    )


@router.post("/verify", response_model=VerifyCodeResponse)
async def verify_code(
    body: VerifyCodeRequest,
    pos_terminal_id: PosTerminalId,
    session: DBSession,
) -> VerifyCodeResponse:
    """Weryfikacja kodu OTP przez terminal POS."""
    try:
        token, discount, discount_pct, net, code_id = await codes_domain.verify_code(
            session,
            body.code,
            body.gross_amount_pln,
            pos_terminal_id,
            body.pos_transaction_ref,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return VerifyCodeResponse(
        verification_token=token,
        discount_amount_pln=discount,
        discount_pct=discount_pct,
        net_amount_pln=net,
        code_id=code_id,
    )


@router.post("/finalize", response_model=FinalizeCodeResponse)
async def finalize_code(
    body: FinalizeCodeRequest,
    session: DBSession,
) -> FinalizeCodeResponse:
    """Finalizacja transakcji po stronie API."""
    try:
        tx = await tx_domain.finalize_transaction(
            session, body.verification_token, body.pos_transaction_ref
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return FinalizeCodeResponse(
        transaction_id=tx.id,
        balance_after_pln=float(tx.balance_after_pln),
        discount_amount_pln=float(tx.discount_amount_pln),
    )


@router.post("/refund", response_model=RefundResponse)
async def refund_code(
    body: RefundRequest,
    current_user: CurrentUser,
    pos_terminal_id: PosTerminalId,
    session: DBSession,
) -> RefundResponse:
    """Zwrot transakcji w oknie 48h."""
    try:
        tx = await tx_domain.process_refund(
            session,
            current_user,
            body.original_transaction_id,
            pos_terminal_id,
            body.pos_transaction_ref,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return RefundResponse(
        transaction_id=tx.id,
        balance_after_pln=float(tx.balance_after_pln),
        refunded_amount_pln=float(tx.discount_amount_pln),
    )
