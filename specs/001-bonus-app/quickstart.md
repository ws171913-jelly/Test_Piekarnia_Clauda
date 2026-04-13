# Quickstart dla deweloperów: BonusApp

**Data**: 2026-04-10 | **Gałąź**: `001-bonus-app`

---

## Wymagania wstępne

- Docker Desktop 4.x+ (z Docker Compose V2)
- Python 3.12+ (backend)
- Node.js 20 LTS + npm (frontend mobile)
- React Native CLI + Android Studio / Xcode (dla symulatora mobile)

---

## 1. Sklonuj i uruchom backend

```bash
git clone <repo-url>
cd Test_Piekarnia_Clauda
git checkout 001-bonus-app

# Uruchom bazę danych i API lokalnie
docker compose up -d postgres
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head          # zastosuj migracje
uvicorn src.main:app --reload # API na http://localhost:8000
```

Dokumentacja OpenAPI dostępna pod: `http://localhost:8000/docs`

---

## 2. Uruchom frontend (React Native)

```bash
cd mobile
npm install
npx react-native start        # Metro bundler
# W osobnym terminalu:
npx react-native run-android  # lub run-ios
```

Aplikacja łączy się z API pod `http://10.0.2.2:8000` (emulator Android)
lub `http://localhost:8000` (symulator iOS).

---

## 3. Uruchom testy

```bash
# Testy backend
cd backend
pytest                         # wszystkie testy
pytest tests/contract/         # tylko kontraktowe
pytest tests/integration/      # tylko integracyjne

# Testy frontend
cd mobile
npm test
```

---

## 4. Symulacja pełnego przebiegu zakupu

### Krok 1 — Zaloguj pracownika i wygeneruj kod

```bash
# Zaloguj się (zwraca JWT) — EMP001 z PIN 1234 (z seed danych)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"hr_employee_id": "EMP001", "pin": "1234"}'

# Wygeneruj kod (użyj tokenu z powyżej)
curl -X POST http://localhost:8000/api/v1/codes \
  -H "Authorization: Bearer <jwt>"
# → {"code": "482931", "expires_at": "...", "balance_pln": "150.00", ...}
```

### Krok 2 — Symuluj weryfikację POS

```bash
curl -X POST http://localhost:8000/api/v1/codes/verify \
  -H "X-POS-API-Key: pos-key-terminal-001" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "482931",
    "pos_transaction_ref": "TEST-001",
    "gross_amount_pln": "100.00"
  }'
# → {"status": "ZATWIERDZONE", "discount_amount_pln": "15.00", ...}
```

### Krok 3 — Finalizuj transakcję

```bash
curl -X POST http://localhost:8000/api/v1/codes/finalize \
  -H "X-POS-API-Key: pos-key-terminal-001" \
  -H "Content-Type: application/json" \
  -d '{
    "verification_token": "<token z verify>",
    "pos_transaction_ref": "TEST-001"
  }'
# → {"status": "SFINALIZOWANE", "balance_after_pln": "135.00"}
```

---

## 5. Dane testowe (seed)

```bash
cd backend
python scripts/seed_dev_data.py
```

Tworzy:
- 3 koszyki (10%, 15%, 20% rabatu)
- 5 testowych pracowników z saldami
- 2 terminale POS z kluczami API (`dev-pos-key-001`, `dev-pos-key-002`)

---

## 6. Symulacja webhooka HR

```bash
# Doładowanie salda pracownika
curl -X POST http://localhost:8000/api/v1/hr/events \
  -H "X-HR-Signature: sha256=<oblicz_lokalnie>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "DOŁADOWANIE",
    "event_id": "test-evt-001",
    "occurred_at": "2026-04-01T00:00:00Z",
    "payload": {
      "hr_employee_id": "EMP-00001",
      "amount_pln": "200.00",
      "balance_expiry_date": "2026-04-30"
    }
  }'
```

Skrypt pomocniczy do generowania podpisu HMAC: `backend/scripts/sign_webhook.py`

---

## Struktura katalogów

```text
backend/
├── src/
│   ├── api/          # Routery FastAPI (endpointy)
│   ├── domain/       # Logika biznesowa (reguły, serwisy domenowe)
│   ├── models/       # Modele SQLAlchemy
│   └── main.py       # Punkt wejścia aplikacji
├── tests/
│   ├── contract/     # Testy kontraktowe Schemathesis
│   ├── integration/  # Testy integracyjne (prawdziwa baza)
│   └── unit/         # Testy jednostkowe domeny
├── alembic/          # Migracje bazy danych
└── scripts/          # Narzędzia deweloperskie (seed, sign_webhook)

mobile/
├── src/
│   ├── screens/      # Ekrany (Balance, History, CodeDisplay)
│   ├── components/   # Współdzielone komponenty UI
│   ├── services/     # Klient API + logika synchronizacji
│   └── store/        # Lokalny stan (AsyncStorage/MMKV)
└── tests/
```
