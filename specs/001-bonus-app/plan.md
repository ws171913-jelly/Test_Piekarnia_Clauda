# Plan implementacji: BonusApp — Subsystem benefitów pracowniczych

**Gałąź**: `001-bonus-app` | **Data**: 2026-04-10 | **Spec**: [spec.md](spec.md)
**Wejście**: Specyfikacja funkcjonalna z `specs/001-bonus-app/spec.md`

## Podsumowanie

System umożliwia pracownikom fizycznych placówek pracodawcy korzystanie z przydzielonych
środków bonusowych przy zakupach w tych placówkach. Pracownik generuje jednorazowy 6-cyfrowy
kod OTP w aplikacji mobilnej; kasjer wprowadza go do terminala POS, który odpytuje API
BonusApp o zatwierdzenie i kwotę rabatu. Po finalizacji sprzedaży API aktualizuje saldo
pracownika atomowo i rejestruje immutowalną Transakcję.

Stos technologiczny: Python 3.12 + FastAPI (backend REST API), PostgreSQL 16 (baza danych),
React Native 0.74+ (aplikacja mobilna iOS/Android), Docker (konteneryzacja).
Integracje: system HR/płacowy (webhook inbound HMAC-SHA256) + system POS (klucz API per-terminal).

## Kontekst techniczny

**Język/Wersja**: Python 3.12 (backend), TypeScript / React Native 0.74+ (mobile)
**Główne zależności**: FastAPI 0.111+, SQLAlchemy 2.x (async), Alembic, Pydantic v2,
  React Native, React Navigation, MMKV (cache offline)
**Storage**: PostgreSQL 16+ (dane transakcyjne i operacyjne)
**Testowanie**: pytest + pytest-asyncio (backend), Jest + React Native Testing Library (mobile),
  Schemathesis (testy kontraktowe OpenAPI)
**Platforma docelowa**: Linux server / Docker (API), iOS 16+ i Android 11+ (aplikacja mobilna)
**Typ projektu**: Web service (REST API) + aplikacja mobilna
**Cele wydajnościowe**: Odpowiedź API do POS < 3 s (KS-002); generowanie kodu < 30 s (KS-001)
**Ograniczenia**: Atomowe transakcje bazodanowe przy każdej modyfikacji salda;
  pesymistyczne blokowanie wiersza przy weryfikacji kodu; TLS obowiązkowy;
  brak obsługi offline dla generowania kodów
**Skala/Zakres**: Docelowo < 10 000 pracowników; < 50 terminali POS; ~1 000 transakcji/dzień

## Weryfikacja Konstytucji

*BRAMA: Musi przejść przed Fazą 0. Ponowna weryfikacja po Fazie 1.*

| Zasada | Status | Uwagi |
|--------|--------|-------|
| I. Domain-Driven Design | ✅ ZALICZONE | Encje Koszyk, Kod autoryzacyjny, Transakcja odpowiadają pojęciom biznesowym placówki. Reguły biznesowe (karencja, blokada salda) są w warstwie domenowej. |
| II. API-First | ✅ ZALICZONE | Wszystkie funkcje eksponowane przez REST API z kontraktami OpenAPI w `contracts/`. Wersjonowanie w URL (`/api/v1/`). |
| III. Test-First | ✅ ZALICZONE | Zadania implementacyjne generowane z założeniem TDD: testy kontraktowe i integracyjne pisane przed implementacją. Wymóg Red-Green-Refactor. |
| IV. Data Integrity & Auditability | ✅ ZALICZONE | Transakcje atomowe z `SELECT FOR UPDATE`; immutowalne rekordy Transakcji; pola `balance_before`/`balance_after` w każdej transakcji; soft-delete dla Users i Baskets. |
| V. Simplicity & Incremental Delivery | ✅ ZALICZONE | 3 niezależne historie (P1 → P2 → P3); każda dostarczalna i weryfikowalna oddzielnie. Brak spekulatywnych abstrakcji. |

**Weryfikacja po Fazie 1**: ✅ Bez zmian — projekt danych i kontrakty nie naruszają żadnej zasady.

## Struktura projektu

### Dokumentacja (ta funkcjonalność)

```text
specs/001-bonus-app/
├── plan.md              # Ten plik
├── research.md          # Decyzje techniczne (Faza 0)
├── data-model.md        # Model danych (Faza 1)
├── quickstart.md        # Przewodnik dewelopera (Faza 1)
├── contracts/
│   ├── api-auth-codes.md   # Endpointy: generowanie, weryfikacja, finalizacja kodów
│   ├── api-users.md        # Endpointy: saldo i historia transakcji
│   └── api-hr-webhook.md   # Webhook HR + endpoint zwrotu POS
├── checklists/
│   └── requirements.md  # Lista kontrolna jakości specyfikacji
└── tasks.md             # Zadania implementacyjne (generowane przez /speckit.tasks)
```

### Kod źródłowy (korzeń repozytorium)

```text
backend/
├── src/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── codes.py        # POST /codes, /codes/verify, /codes/finalize, /codes/refund
│   │   │   ├── users.py        # GET /users/me, /users/me/transactions
│   │   │   └── hr_events.py    # POST /hr/events
│   │   └── deps.py             # Zależności FastAPI (auth, db session)
│   ├── domain/
│   │   ├── codes.py            # Logika generowania i weryfikacji OTP
│   │   ├── transactions.py     # Logika obliczania rabatu, finalizacji, zwrotów
│   │   └── hr_processor.py     # Przetwarzanie zdarzeń HR
│   ├── models/
│   │   ├── user.py             # Model SQLAlchemy: users
│   │   ├── basket.py           # Model SQLAlchemy: baskets
│   │   ├── auth_code.py        # Model SQLAlchemy: auth_codes
│   │   ├── transaction.py      # Model SQLAlchemy: transactions
│   │   └── hr_event.py         # Model SQLAlchemy: hr_events
│   ├── schemas/                # Modele Pydantic (request/response)
│   └── main.py                 # Punkt wejścia FastAPI
├── tests/
│   ├── contract/               # Schemathesis + testy ręczne kontraktów API
│   ├── integration/            # Testy integracyjne (prawdziwa baza PostgreSQL)
│   └── unit/                   # Testy jednostkowe logiki domenowej
├── alembic/                    # Migracje bazy danych
└── scripts/
    ├── seed_dev_data.py
    └── sign_webhook.py

mobile/
├── src/
│   ├── screens/
│   │   ├── BalanceScreen.tsx       # Saldo + data ważności + koszyk
│   │   ├── CodeDisplayScreen.tsx   # Wyświetlanie kodu OTP i odliczanie TTL
│   │   └── HistoryScreen.tsx       # Lista transakcji (paginacja)
│   ├── components/                 # Współdzielone UI
│   ├── services/
│   │   ├── api.ts                  # Klient HTTP (axios/fetch)
│   │   └── sync.ts                 # Synchronizacja cache offline
│   └── store/
│       └── userStore.ts            # Lokalny stan (MMKV)
└── tests/

docker-compose.yml              # PostgreSQL + API (środowisko lokalne)
```

**Decyzja strukturalna**: Opcja 3 (Mobile + API). Backend jako samodzielny serwis REST,
frontend jako natywna aplikacja React Native. Uzasadnienie: pracownicy używają systemu
w ruchu, przy kasie; offline cache (KS-007) jest naturalnie obsługiwany przez MMKV.

## Śledzenie złożoności

> Sekcja pusta — Weryfikacja Konstytucji nie wykazała naruszeń wymagających uzasadnienia.
