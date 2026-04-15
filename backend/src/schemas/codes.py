import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerateCodeResponse(BaseModel):
    code: str = Field(..., description="6-cyfrowy kod OTP")
    expires_at: datetime
    code_id: uuid.UUID


class VerifyCodeRequest(BaseModel):
    code: str = Field(..., description="6-cyfrowy kod OTP wpisany przez kasjera")
    pos_transaction_ref: str | None = None
    gross_amount_pln: float = Field(..., gt=0)


class VerifyCodeResponse(BaseModel):
    verification_token: str
    discount_amount_pln: float
    discount_pct: float
    net_amount_pln: float
    code_id: uuid.UUID


class FinalizeCodeRequest(BaseModel):
    verification_token: str
    pos_transaction_ref: str | None = None


class FinalizeCodeResponse(BaseModel):
    transaction_id: uuid.UUID
    balance_after_pln: float
    discount_amount_pln: float


class RefundRequest(BaseModel):
    original_transaction_id: uuid.UUID
    pos_transaction_ref: str | None = None


class RefundResponse(BaseModel):
    transaction_id: uuid.UUID
    balance_after_pln: float
    refunded_amount_pln: float
