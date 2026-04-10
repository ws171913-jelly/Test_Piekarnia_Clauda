---
description: "Lista zadań implementacyjnych — BonusApp"
---

# Zadania: BonusApp — Subsystem benefitów pracowniczych

**Wejście**: Dokumenty projektowe z `specs/001-bonus-app/`
**Wymagania wstępne**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅

**Testy**: Uwzględnione zgodnie z Zasadą III Konstytucji (Test-First NON-NEGOTIABLE).
Testy MUSZĄ być napisane i CZERWONE przed przystąpieniem do implementacji.

**Organizacja**: Zadania pogrupowane według historii użytkownika, umożliwiając niezależną
implementację i testowanie każdej historii.

## Format: `[ID] [P?] [US?] Opis`

- **[P]**: Można uruchamiać równolegle (różne pliki, brak zależności)
- **[US]**: Która historia użytkownika (US1, US2, US3)
- Każde zadanie zawiera dokładną ścieżkę pliku

## Konwencje ścieżek

- Backend: `backend/src/`, `backend/tests/`
- Frontend mobile: `mobile/src/`, `mobile/tests/`
- Infrastruktura: korzeń repozytorium

---

## Faza 1: Konfiguracja (Infrastruktura wspólna)

**Cel**: Inicjalizacja struktury projektu i środowiska deweloperskiego

- [ ] T001 Utwórz strukturę katalogów projektu zgodnie z planem implementacji (`backend/`, `mobile/`, `docker-compose.yml`)
- [ ] T002 [P] Zainicjalizuj projekt backend: Python 3.12 venv, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic v2 (`backend/requirements.txt`, `backend/pyproject.toml`)
- [ ] T003 [P] Zainicjalizuj projekt frontend: React Native 0.74+, TypeScript strict, MMKV, React Navigation (`mobile/package.json`, `mobile/tsconfig.json`)
- [ ] T004 [P] Skonfiguruj linting i formatowanie: black + mypy (backend), ESLint + Prettier (mobile) (`backend/pyproject.toml`, `mobile/.eslintrc.js`)
- [ ] T005 [P] Utwórz `docker-compose.yml` z PostgreSQL 16 i serwisem API (`docker-compose.yml`)
- [ ] T006 Utwórz punkt wejścia FastAPI z konfiguracją CORS i obsługą wyjątków (`backend/src/main.py`)

---

## Faza 2: Fundament (Blokujące warunki wstępne)

**Cel**: Infrastruktura core wymagana zanim jakakolwiek historia użytkownika może ruszyć

**⚠️ KRYTYCZNE**: Żadna historia użytkownika nie może się rozpocząć przed ukończeniem tej fazy

- [ ] T007 Utwórz modele SQLAlchemy: `User`, `Basket` (`backend/src/models/user.py`, `backend/src/models/basket.py`)
- [ ] T008 [P] Utwórz modele SQLAlchemy: `AuthCode`, `Transaction`, `HrEvent` (`backend/src/models/auth_code.py`, `backend/src/models/transaction.py`, `backend/src/models/hr_event.py`)
- [ ] T009 Skonfiguruj async engine i sesję SQLAlchemy (`backend/src/database.py`)
- [ ] T010 Utwórz migracje Alembic dla wszystkich tabel: users, baskets, auth_codes, transactions, hr_events (`backend/alembic/versions/001_initial_schema.py`)
- [ ] T011 Zaimplementuj zależność uwierzytelniania JWT (weryfikacja tokenu Bearer) (`backend/src/api/deps.py`)
- [ ] T012 [P] Zaimplementuj zależność uwierzytelniania POS (walidacja klucza `X-POS-API-Key`) (`backend/src/api/deps.py`)
- [ ] T013 [P] Skonfiguruj globalny handler błędów i kody odpowiedzi domenowych (`backend/src/api/errors.py`)
- [ ] T014 Utwórz skrypt seed danych deweloperskich: 3 koszyki, 5 pracowników, 2 terminale POS (`backend/scripts/seed_dev_data.py`)

**Punkt kontrolny**: Fundament gotowy — można uruchamiać historię US1

---

## Faza 3: Historia użytkownika 1 — Przebieg zakupu z rabatem (Priorytet: P1) 🎯 MVP

**Cel**: Pracownik generuje kod → kasjer weryfikuje → POS finalizuje → saldo zaktualizowane

**Niezależny test**: Uruchom `seed_dev_data.py`, wywołaj `POST /codes` z tokenem JWT,
`POST /codes/verify` z kluczem POS, `POST /codes/finalize` — zweryfikuj saldo i rekord transakcji.

### Testy dla US1 — pisać PRZED implementacją ⚠️

> **UWAGA: Napisz te testy PRZED implementacją i upewnij się, że CZERWIEJĄ**

- [ ] T015 [P] [US1] Test kontraktowy: `POST /api/v1/codes` — scenariusze zatwierdzenia i błędów (`backend/tests/contract/test_codes_generate.py`)
- [ ] T016 [P] [US1] Test kontraktowy: `POST /api/v1/codes/verify` — zatwierdzenie, wygasły, wykorzystany, niewystarczające saldo (`backend/tests/contract/test_codes_verify.py`)
- [ ] T017 [P] [US1] Test kontraktowy: `POST /api/v1/codes/finalize` — finalizacja i idempotencja (`backend/tests/contract/test_codes_finalize.py`)
- [ ] T018 [P] [US1] Test integracyjny: pełny przebieg zakupu — generowanie → weryfikacja → finalizacja → weryfikacja salda (`backend/tests/integration/test_purchase_flow.py`)
- [ ] T019 [P] [US1] Test jednostkowy: logika generowania OTP — format 6-cyfrowy, hash bcrypt (`backend/tests/unit/test_code_generation.py`)
- [ ] T020 [P] [US1] Test jednostkowy: obliczanie rabatu — `min(saldo, floor(kwota × pct))`, limit miesięczny (`backend/tests/unit/test_discount_calculation.py`)

### Implementacja US1

- [ ] T021 [P] [US1] Schematy Pydantic: żądania i odpowiedzi dla kodów OTP (`backend/src/schemas/codes.py`)
- [ ] T022 [P] [US1] Serwis domenowy: generowanie kodu — kryptograficzny OTP 6-cyfrowy, hash bcrypt, zapis w `auth_codes` (`backend/src/domain/codes.py`)
- [ ] T023 [US1] Serwis domenowy: weryfikacja kodu przy POS — `SELECT FOR UPDATE`, sprawdzenie statusu, obliczenie rabatu, `verification_token` JWT (`backend/src/domain/codes.py`)
- [ ] T024 [US1] Serwis domenowy: finalizacja transakcji — atomowy UPDATE salda + INSERT transaction + zmiana statusu kodu na WYKORZYSTANY (`backend/src/domain/transactions.py`)
- [ ] T025 [US1] Router API: `POST /api/v1/codes` — generowanie kodu dla zalogowanego pracownika (`backend/src/api/v1/codes.py`)
- [ ] T026 [US1] Router API: `POST /api/v1/codes/verify` — weryfikacja przez terminal POS (`backend/src/api/v1/codes.py`)
- [ ] T027 [US1] Router API: `POST /api/v1/codes/finalize` — finalizacja po stronie API (`backend/src/api/v1/codes.py`)
- [ ] T028 [P] [US1] Ekran wyświetlania kodu OTP z odliczaniem TTL (`mobile/src/screens/CodeDisplayScreen.tsx`)
- [ ] T029 [US1] Klient API mobilny: wywołanie `POST /codes` + obsługa błędów karencji/salda (`mobile/src/services/api.ts`)
- [ ] T030 [P] [US1] Test ekranu CodeDisplayScreen: renderowanie kodu i odliczania (`mobile/tests/CodeDisplayScreen.test.tsx`)

**Punkt kontrolny**: US1 w pełni funkcjonalna i niezależnie testowalna — MVP gotowe

---

## Faza 4: Historia użytkownika 2 — Podgląd salda i historii transakcji (Priorytet: P2)

**Cel**: Pracownik widzi saldo, koszyk, datę ważności i historię — również offline

**Niezależny test**: Zaloguj pracownika, wywołaj `GET /users/me` i `GET /users/me/transactions`,
wyłącz sieć w emulatorze — zweryfikuj wyświetlanie danych z cache.

### Testy dla US2 — pisać PRZED implementacją ⚠️

- [ ] T031 [P] [US2] Test kontraktowy: `GET /api/v1/users/me` — struktura odpowiedzi i pola (`backend/tests/contract/test_users_profile.py`)
- [ ] T032 [P] [US2] Test kontraktowy: `GET /api/v1/users/me/transactions` — paginacja, filtrowanie po typie (`backend/tests/contract/test_users_transactions.py`)
- [ ] T033 [P] [US2] Test integracyjny: historia po wielu transakcjach — kolejność, paginacja (`backend/tests/integration/test_transaction_history.py`)
- [ ] T034 [P] [US2] Test cache offline: dane wyświetlają się bez sieci przez 24h (`mobile/tests/offlineCache.test.ts`)

### Implementacja US2

- [ ] T035 [P] [US2] Schematy Pydantic: odpowiedzi profilu i historii transakcji (`backend/src/schemas/users.py`)
- [ ] T036 [US2] Router API: `GET /api/v1/users/me` — profil operacyjny pracownika (`backend/src/api/v1/users.py`)
- [ ] T037 [US2] Router API: `GET /api/v1/users/me/transactions` — historia paginowana z filtrowaniem (`backend/src/api/v1/users.py`)
- [ ] T038 [P] [US2] Ekran salda: saldo, procent koszyka, data ważności (`mobile/src/screens/BalanceScreen.tsx`)
- [ ] T039 [P] [US2] Ekran historii transakcji: lista paginowana (ZAKUP/ZWROT) (`mobile/src/screens/HistoryScreen.tsx`)
- [ ] T040 [US2] Logika synchronizacji cache offline: sync przy starcie aplikacji + wskaźnik „Ostatnia aktualizacja" (`mobile/src/services/sync.ts`)
- [ ] T041 [US2] Lokalny store MMKV: `UserSession`, `TransactionHistoryLite` (`mobile/src/store/userStore.ts`)

**Punkt kontrolny**: US1 i US2 działają niezależnie — pracownik widzi saldo i historię

---

## Faza 5: Historia użytkownika 3 — Zabezpieczenia antyszachrajskie i bezpieczeństwo kodów (Priorytet: P3)

**Cel**: Karencja, blokada zerowego salda, ochrona przed wyścigiem, wygasanie, integracja HR, zwroty

**Niezależny test**: Wygeneruj kod przy saldzie 0 (oczekiwany błąd), wyślij dwa jednoczesne żądania POS
dla tego samego kodu (jedno zatwierdzenie), wyślij webhook HR DOŁADOWANIE, zweryfikuj saldo.

### Testy dla US3 — pisać PRZED implementacją ⚠️

- [ ] T042 [P] [US3] Test jednostkowy: karencja — blokada gdy `last_code_generated_at` < 30 min temu (`backend/tests/unit/test_cooldown.py`)
- [ ] T043 [P] [US3] Test jednostkowy: blokada przy saldzie = 0 PLN (`backend/tests/unit/test_zero_balance_block.py`)
- [ ] T044 [P] [US3] Test integracyjny: wyścig procesów — dwa jednoczesne `POST /codes/verify` dla tego samego kodu (`backend/tests/integration/test_race_condition.py`)
- [ ] T045 [P] [US3] Test integracyjny: wygasanie kodów — weryfikacja kodu po upływie TTL (`backend/tests/integration/test_code_expiry.py`)
- [ ] T046 [P] [US3] Test integracyjny: webhook HR DOŁADOWANIE — saldo zaktualizowane po zdarzeniu (`backend/tests/integration/test_hr_webhook.py`)
- [ ] T047 [P] [US3] Test integracyjny: zwrot w oknie 48h i po przekroczeniu okna (`backend/tests/integration/test_refund_window.py`)

### Implementacja US3

- [ ] T048 [US3] Rozszerz logikę domenową o walidację karencji 30 min i blokadę zerowego salda (`backend/src/domain/codes.py`)
- [ ] T049 [P] [US3] Zadanie cron: wygasanie aktywnych kodów po TTL — zmiana statusu na WYGASŁY (`backend/src/tasks/expire_codes.py`)
- [ ] T050 [US3] Serwis domenowy: przetwarzanie zdarzeń HR — NOWY_PRACOWNIK, ZMIANA_KOSZYKA, DOŁADOWANIE, KONIEC_OKRESU, DEZAKTYWACJA (`backend/src/domain/hr_processor.py`)
- [ ] T051 [US3] Serwis domenowy: logika zwrotu — walidacja okna 48h, uznanie rabatu, zapis ZWROT (`backend/src/domain/transactions.py`)
- [ ] T052 [P] [US3] Schematy Pydantic: zdarzenia HR i żądanie zwrotu POS (`backend/src/schemas/hr_events.py`)
- [ ] T053 [US3] Router API: `POST /api/v1/hr/events` — odbiór i weryfikacja podpisu HMAC-SHA256 (`backend/src/api/v1/hr_events.py`)
- [ ] T054 [US3] Router API: `POST /api/v1/codes/refund` — zwrot z walidacją okna czasowego (`backend/src/api/v1/codes.py`)
- [ ] T055 [P] [US3] Skrypt pomocniczy: generowanie podpisu HMAC do testów webhooka (`backend/scripts/sign_webhook.py`)

**Punkt kontrolny**: Wszystkie trzy historie działają niezależnie i są odporne na nadużycia

---

## Faza N: Szlif i przekrojowe zagadnienia

**Cel**: Usprawnienia wpływające na wszystkie historie

- [ ] T056 [P] Weryfikacja i uzupełnienie dokumentacji OpenAPI (opisy, przykłady, kody błędów) (`backend/src/main.py`)
- [ ] T057 Walidacja quickstart.md — przebieg end-to-end zgodnie z instrukcjami dokumentu (`specs/001-bonus-app/quickstart.md`)
- [ ] T058 [P] Konfiguracja Docker Compose gotowa do produkcji: healthchecks, zmienne env, sekrety (`docker-compose.yml`)
- [ ] T059 [P] Dodatkowe testy jednostkowe dla przypadków brzegowych (wygasła data ważności środków, dezaktywowany pracownik) (`backend/tests/unit/`)
- [ ] T060 [P] Przegląd i refaktoryzacja kodu po zakończeniu wszystkich historii
- [ ] T061 [P] Weryfikacja bezpieczeństwa: nagłówki TLS, obsługa błędów bez ujawniania szczegółów wewnętrznych (`backend/src/`)

---

## Zależności i kolejność wykonania

### Zależności faz

- **Faza 1 (Konfiguracja)**: Brak zależności — można zacząć natychmiast
- **Faza 2 (Fundament)**: Zależy od ukończenia Fazy 1 — **BLOKUJE wszystkie historie użytkownika**
- **Faza 3 (US1)**: Zależy od Fazy 2 — 🎯 MVP po ukończeniu
- **Faza 4 (US2)**: Zależy od Fazy 2; może równolegle z US1 jeśli wystarczy zasobów
- **Faza 5 (US3)**: Zależy od Fazy 2; buduje na US1 (rozszerza `codes.py`, `transactions.py`)
- **Faza N (Szlif)**: Zależy od ukończenia wybranych historii

### Zależności wewnątrz US1

```
T022 (generowanie kodu)
  → T023 (weryfikacja kodu)      # ta sama klasa domenowa
    → T024 (finalizacja)         # zależy od kodu zweryfikowanego
      → T025 (router /codes)
      → T026 (router /verify)
      → T027 (router /finalize)
T028 (ekran mobile) ← T029 (klient API mobile)
```

### Zależności wewnątrz US3

```
T048 (rozszerzenie codes.py)     # zależy od T022-T023 z US1
T050 (hr_processor)              # niezależny od US1
T051 (logika zwrotu)             # zależy od T024 z US1
T053 (router hr/events)          # zależy od T050
T054 (router /refund)            # zależy od T051
```

### Możliwości równoległe

- Faza 1: T002, T003, T004, T005 można uruchamiać równolegle
- Faza 2: T007+T008 równolegle; T010 po T007-T008; T011+T012+T013 równolegle
- Testy US1 (T015–T020): wszystkie równolegle przed implementacją
- Modele i schematy w każdej historii: równolegle między sobą
- US2 i US3 można pracować równolegle po ukończeniu Fazy 2 (jeśli różne osoby)

---

## Przykład równoległego wykonania — US1

```bash
# Uruchom wszystkie testy US1 jednocześnie (muszą CZERWIENIEĆ):
Zadanie: "Test kontraktowy POST /codes" (T015)
Zadanie: "Test kontraktowy POST /codes/verify" (T016)
Zadanie: "Test kontraktowy POST /codes/finalize" (T017)
Zadanie: "Test jednostkowy generowanie OTP" (T019)
Zadanie: "Test jednostkowy obliczanie rabatu" (T020)

# Po czerwonych testach — implementacja domenowa:
Zadanie: "Serwis domenowy: generowanie kodu" (T022)
# Następnie sekwencyjnie:
Zadanie: "Serwis domenowy: weryfikacja kodu" (T023)
Zadanie: "Serwis domenowy: finalizacja" (T024)

# Równolegle z implementacją backend — mobile:
Zadanie: "Ekran CodeDisplayScreen" (T028)
Zadanie: "Test ekranu CodeDisplayScreen" (T030)
```

---

## Strategia implementacji

### MVP Najpierw (tylko US1)

1. Ukończ Fazę 1: Konfiguracja
2. Ukończ Fazę 2: Fundament (**KRYTYCZNE** — blokuje wszystko)
3. Napisz testy US1 (T015–T020) i upewnij się, że CZERWIEJĄ
4. Ukończ Fazę 3: US1
5. **ZATRZYMAJ I ZWALIDUJ**: Przetestuj US1 niezależnie (pełny przebieg zakupu)
6. Demonstracja MVP

### Dostawa inkrementalna

1. Faza 1 + Faza 2 → Fundament gotowy
2. US1 → Przetestuj niezależnie → MVP
3. US2 → Przetestuj niezależnie (saldo + offline)
4. US3 → Przetestuj niezależnie (zabezpieczenia + HR + zwroty)
5. Szlif → Gotowe do produkcji

### Strategia równoległego zespołu

Z dwoma lub więcej deweloperami — po ukończeniu Fazy 2:

- Deweloper A: US1 (backend: codes.py, transactions.py, router)
- Deweloper B: US2 (backend: users.py + mobile: BalanceScreen, HistoryScreen)
- Po US1+US2: US3 razem (zabezpieczenia, HR, zwroty)

---

## Uwagi

- `[P]` = różne pliki, brak zależności — można uruchamiać równolegle
- `[US]` mapuje zadanie do konkretnej historii użytkownika dla śledzenia
- Testy MUSZĄ być napisane i CZERWONE przed implementacją (Konstytucja Zasada III)
- Commity po każdym zadaniu lub logicznej grupie
- Zatrzymaj się na każdym punkcie kontrolnym, aby zwalidować historię niezależnie
- Unikaj: niejasnych zadań, konfliktów na tym samym pliku, zależności między historiami
  które naruszają ich niezależność
