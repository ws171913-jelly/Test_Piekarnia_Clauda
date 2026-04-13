from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import register_exception_handlers
from src.api.v1 import auth, codes, hr_events, users
from src.config import settings

app = FastAPI(
    title="BonusApp API",
    description=(
        "Subsystem benefitów pracowniczych dla placówek rzemieślniczych.\n\n"
        "## Uwierzytelnianie\n\n"
        "Większość endpointów wymaga nagłówka `Authorization: Bearer <JWT>`.\n"
        "Token uzyskuje się przez `POST /api/v1/auth/login` (TTL: 8h).\n"
        "Terminale POS używają nagłówka `X-POS-API-Key`.\n\n"
        "## Kody błędów\n\n"
        "- `400 Bad Request` — nieprawidłowe dane wejściowe\n"
        "- `401 Unauthorized` — brak lub nieważny token JWT\n"
        "- `403 Forbidden` — brak uprawnień (np. brak klucza POS)\n"
        "- `404 Not Found` — zasób nie istnieje\n"
        "- `409 Conflict` — konflikt (np. idempotentna finalizacja)\n"
        "- `422 Unprocessable Entity` — błąd biznesowy (karencja, zerowe saldo, blokada)\n"
        "- `500 Internal Server Error` — błąd serwera\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Logowanie pracownika PIN-em i zmiana PIN-u.",
        },
        {
            "name": "codes",
            "description": (
                "Generowanie, weryfikacja i finalizacja kodów rabatowych OTP. "
                "Zawiera też endpoint zwrotu."
            ),
        },
        {
            "name": "users",
            "description": "Profil pracownika i historia transakcji.",
        },
        {
            "name": "hr",
            "description": "Webhook zdarzeń HR (HMAC-SHA256): doładowania, zmiany koszyka, resety PIN, itp.",
        },
        {
            "name": "system",
            "description": "Healthcheck i diagnostyka.",
        },
    ],
)

_DEV = settings.environment == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _DEV else ["https://bonusapp.internal"],
    allow_origin_regex=r"http://localhost:\d+" if _DEV else None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-POS-API-Key", "X-HR-Signature"],
)

register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(codes.router, prefix="/api/v1/codes", tags=["codes"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(hr_events.router, prefix="/api/v1/hr", tags=["hr"])


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
