from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import register_exception_handlers
from src.api.v1 import auth, codes, hr_events, users

app = FastAPI(
    title="BonusApp API",
    description="Subsystem benefitów pracowniczych dla placówek rzemieślniczych",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(codes.router, prefix="/api/v1/codes", tags=["codes"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(hr_events.router, prefix="/api/v1/hr", tags=["hr"])


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
