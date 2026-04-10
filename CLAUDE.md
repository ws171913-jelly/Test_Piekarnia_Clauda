# Test_Piekarnia_Clauda — Wytyczne dla Claude Code

Wygenerowano automatycznie na podstawie planów funkcjonalności. Ostatnia aktualizacja: 2026-04-10

## Aktywne technologie

- **Backend**: Python 3.12, FastAPI 0.111+, SQLAlchemy 2.x (async), Alembic, Pydantic v2
- **Frontend**: TypeScript, React Native 0.74+, MMKV
- **Baza danych**: PostgreSQL 16+
- **Testowanie**: pytest, pytest-asyncio, Schemathesis, Jest, React Native Testing Library
- **Infrastruktura**: Docker, Docker Compose

## Struktura projektu

```text
backend/
├── src/
│   ├── api/v1/       # Routery FastAPI
│   ├── domain/       # Logika biznesowa
│   ├── models/       # Modele SQLAlchemy
│   └── schemas/      # Modele Pydantic
├── tests/
│   ├── contract/     # Testy kontraktowe (Schemathesis)
│   ├── integration/  # Testy integracyjne (prawdziwa baza)
│   └── unit/         # Testy jednostkowe
└── alembic/          # Migracje

mobile/
├── src/
│   ├── screens/      # Ekrany aplikacji
│   ├── services/     # Klient API + synchronizacja
│   └── store/        # Cache offline (MMKV)
└── tests/
```

## Komendy

```bash
# Backend
cd backend && uvicorn src.main:app --reload   # uruchom API
cd backend && pytest                           # wszystkie testy
cd backend && alembic upgrade head             # zastosuj migracje

# Frontend
cd mobile && npx react-native start            # Metro bundler
cd mobile && npm test                          # testy

# Infrastruktura
docker compose up -d postgres                  # baza lokalna
```

## Styl kodu

- Python: PEP 8, typy statyczne (mypy), formatowanie black
- TypeScript: strict mode, ESLint + Prettier
- Wszystkie operacje modyfikujące saldo w transakcjach bazy z `SELECT FOR UPDATE`
- Immutowalne rekordy transakcji — brak UPDATE na tabeli `transactions`
- Soft-delete dla `users` i `baskets` — twarde usuwanie zabronione

## Ostatnie zmiany

- `001-bonus-app`: Dodano BonusApp — Subsystem benefitów pracowniczych
  (Python/FastAPI + React Native + PostgreSQL)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
