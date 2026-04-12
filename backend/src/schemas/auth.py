from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    hr_employee_id: str = Field(..., description="Numer pracownika w systemie HR")
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d{4,6}$")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_pin: bool = False


class ChangePinRequest(BaseModel):
    new_pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d{4,6}$")
    confirm_pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d{4,6}$")


class ChangePinResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
