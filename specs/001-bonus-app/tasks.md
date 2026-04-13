---
description: "Lista zadań implementacyjnych — BonusApp"
---

# Zadania: BonusApp — Subsystem benefitów pracowniczych

**Wejście**: Dokumenty projektowe z `specs/001-bonus-app/`
**Wymagania wstępne**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, research.md ✅
**Ostatnia aktualizacja**: 2026-04-10 — dodano zadania auth (WF-016/017/019) i retencji (WF-018)

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

- [X] T001 Utwórz strukturę katalogów projektu zgodnie z planem implementacji (`backend/`, `mobile/`, `docker-compose.yml`)
- [X] T002 [P] Zainicjalizuj projekt backend: Python 3.12 venv, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic v2 (`backend/requirements.txt`, `backend/pyproject.toml`)
- [X] T003 [P] Zainicjalizuj projekt frontend: React Native 0.74+, TypeScript strict, MMKV, React Navigation (`mobile/package.json`, `mobile/tsconfig.json`)
- [X] T004 [P] Skonfiguruj linting i formatowanie: black + mypy (backend), ESLint + Prettier (mobile) (`backend/pyproject.toml`, `mobile/.eslintrc.js`)
- [X] T005 [P] Utwórz `docker-compose.yml` z PostgreSQL 16 i serwisem API (`docker-compose.yml`)
- [X] T006 Utwórz punkt wejścia FastAPI z konfiguracją CORS i obsługą wyjątków (`backend/src/main.py`)

---

## Faza 2: Fundament (Blokujące warunki wstępne)

**Cel**: Infrastruktura core wymagana zanim jakakolwiek historia użytkownika może ruszyć

**⚠️ KRYTYCZNE**: Żadna historia użytkownika nie może się rozpocząć przed ukończeniem tej fazy

### Modele i baza danych

- [X] T007 Utwórz model SQLAlchemy `User` z polami auth: `pin_hash` (bcrypt), `login_attempts`, `locked_until`, `must_change_pin` (bool), `current_jti` (UUID); utwórz model `Basket` (`backend/src/models/user.py`, `backend/src/models/basket.py`)
- [X] T008 [P] Utwórz modele SQLAlchemy: `AuthCode`, `Transaction`, `HrEvent` (`backend/src/models/auth_code.py`, `backend/src/models/transaction.py`, `backend/src/models/hr_event.py`)
- [X] T009 Skonfiguruj async engine i sesję SQLAlchemy (`backend/src/database.py`)
- [X] T010 Utwórz migracje Alembic dla wszystkich tabel: users (z polami auth), baskets, auth_codes, transactions, hr_events (`backend/alembic/versions/001_initial_schema.py`)

### Uwierzytelnianie pracownika (WF-016, WF-017, WF-019)

- [X] T011 [P] Schematy Pydantic: żądanie logowania (nr pracownika + PIN), odpowiedź z JWT, żądanie zmiany PIN (`backend/src/schemas/auth.py`)
- [X] T012 [P] Test jednostkowy: logika PIN — weryfikacja hash, blokada po 5 próbach, odblokowanie po 15 min, generowanie PIN tymczasowego (onboarding + reset), flaga `must_change_pin`, unieważnienie `jti` przy nowym logowaniu (`backend/tests/unit/test_pin_auth.py`)
- [X] T013 [P] Test integracyjny: pełny przebieg logowania — sukces, błędny PIN ×5, blokada, ponowna próba po 15 min; pierwsze logowanie PIN tymczasowym → wymuszona zmiana → dostęp; nowe logowanie unieważnia poprzednią sesję (`backend/tests/integration/test_auth_flow.py`)
- [X] T014 Serwis domenowy: weryfikacja PIN (bcrypt), licznik nieudanych prób, blokada konta, wydanie JWT z TTL 8h + generowanie `jti` zapisywanego w `users.current_jti`; generowanie PIN tymczasowego (dla NOWY_PRACOWNIK i RESET_PIN) z ustawieniem `must_change_pin = true`; obsługa wymuszonej zmiany PIN (zerowanie flagi i `jti`) (`backend/src/domain/auth.py`)
- [X] T015 Router API: `POST /api/v1/auth/login` (wykrywa `must_change_pin` i zwraca status wymuszonej zmiany) i `POST /api/v1/auth/change-pin` (zeruje `must_change_pin`, wydaje pełny JWT po zmianie) (`backend/src/api/v1/auth.py`)
- [X] T016 [P] Ekran logowania aplikacji mobilnej: formularz nr pracownika + PIN, komunikat blokady z odliczaniem (`mobile/src/screens/LoginScreen.tsx`)
- [X] T017 [P] Test ekranu LoginScreen: renderowanie formularza, komunikat po błędnym PIN, stan blokady (`mobile/tests/LoginScreen.test.tsx`)

### Middleware i infrastruktura API

- [X] T018 Zaimplementuj zależność FastAPI: weryfikacja tokenu JWT Bearer (8h TTL) + walidacja `jti` względem `users.current_jti` w bazie — token z nieaktualnym `jti` MUSI być odrzucony z HTTP 401 (`backend/src/api/deps.py`)
- [X] T019 [P] Zaimplementuj zależność FastAPI: walidacja klucza `X-POS-API-Key` per-terminal (`backend/src/api/deps.py`)
- [X] T020 [P] Skonfiguruj globalny handler błędów i kody odpowiedzi domenowych (`backend/src/api/errors.py`)
- [X] T021 Utwórz skrypt seed danych deweloperskich: 3 koszyki, 5 pracowników z PIN-ami, 2 terminale POS (`backend/scripts/seed_dev_data.py`)

**Punkt kontrolny**: Fundament gotowy (w tym logowanie) — można uruchamiać historię US1

---

## Faza 3: Historia użytkownika 1 — Przebieg zakupu z rabatem (Priorytet: P1) 🎯 MVP

**Cel**: Zalogowany pracownik generuje kod → kasjer weryfikuje → POS finalizuje → saldo zaktualizowane

**Niezależny test**: Zaloguj się (`POST /auth/login`), wygeneruj kod (`POST /codes`),
wywołaj `POST /codes/verify` z kluczem POS, `POST /codes/finalize` —
zweryfikuj saldo i rekord transakcji.

### Testy dla US1 — pisać PRZED implementacją ⚠️

> **UWAGA: Napisz te testy PRZED implementacją i upewnij się, że CZERWIEJĄ**

- [X] T022 [P] [US1] Test kontraktowy: `POST /api/v1/codes` — zatwierdzenie, karencja, zerowe saldo (`backend/tests/contract/test_codes_generate.py`)
- [X] T023 [P] [US1] Test kontraktowy: `POST /api/v1/codes/verify` — zatwierdzenie, wygasły, wykorzystany, niewystarczające saldo (`backend/tests/contract/test_codes_verify.py`)
- [X] T024 [P] [US1] Test kontraktowy: `POST /api/v1/codes/finalize` — finalizacja i idempotencja (`backend/tests/contract/test_codes_finalize.py`)
- [X] T025 [P] [US1] Test integracyjny: pełny przebieg zakupu — generowanie → weryfikacja → finalizacja → weryfikacja salda (`backend/tests/integration/test_purchase_flow.py`)
- [X] T026 [P] [US1] Test jednostkowy: generowanie OTP — format 6-cyfrowy, hash bcrypt (`backend/tests/unit/test_code_generation.py`)
- [X] T027 [P] [US1] Test jednostkowy: obliczanie rabatu — `min(saldo, floor(kwota × pct))`, limit miesięczny (`backend/tests/unit/test_discount_calculation.py`)

### Implementacja US1

- [X] T028 [P] [US1] Schematy Pydantic: żądania i odpowiedzi dla kodów OTP (`backend/src/schemas/codes.py`)
- [X] T029 [P] [US1] Serwis domenowy: generowanie kodu — kryptograficzny OTP 6-cyfrowy, hash bcrypt, zapis w `auth_codes` (`backend/src/domain/codes.py`)
- [X] T030 [US1] Serwis domenowy: weryfikacja kodu przy POS — `SELECT FOR UPDATE`, sprawdzenie statusu, obliczenie rabatu, `verification_token` JWT (`backend/src/domain/codes.py`)
- [X] T031 [US1] Serwis domenowy: finalizacja transakcji — atomowy UPDATE salda + INSERT transaction + zmiana statusu kodu na WYKORZYSTANY (`backend/src/domain/transactions.py`)
- [X] T032 [US1] Router API: `POST /api/v1/codes` — generowanie kodu dla zalogowanego pracownika (`backend/src/api/v1/codes.py`)
- [X] T033 [US1] Router API: `POST /api/v1/codes/verify` — weryfikacja przez terminal POS (`backend/src/api/v1/codes.py`)
- [X] T034 [US1] Router API: `POST /api/v1/codes/finalize` — finalizacja po stronie API (`backend/src/api/v1/codes.py`)
- [X] T035 [P] [US1] Ekran wyświetlania kodu OTP z odliczaniem TTL (`mobile/src/screens/CodeDisplayScreen.tsx`)
- [X] T036 [US1] Klient API mobilny: wywołanie `POST /auth/login` (zapis JWT) + `POST /codes` + obsługa błędów karencji/salda (`mobile/src/services/api.ts`)
- [X] T037 [P] [US1] Test ekranu CodeDisplayScreen: renderowanie kodu i odliczania (`mobile/tests/CodeDisplayScreen.test.tsx`)

**Punkt kontrolny**: US1 w pełni funkcjonalna i niezależnie testowalna — MVP gotowe

---

## Faza 4: Historia użytkownika 2 — Podgląd salda i historii transakcji (Priorytet: P2)

**Cel**: Pracownik widzi saldo, koszyk, datę ważności i historię — również offline

**Niezależny test**: Zaloguj pracownika, wywołaj `GET /users/me` i `GET /users/me/transactions`,
wyłącz sieć w emulatorze — zweryfikuj wyświetlanie danych z cache.

### Testy dla US2 — pisać PRZED implementacją ⚠️

- [X] T038 [P] [US2] Test kontraktowy: `GET /api/v1/users/me` — struktura odpowiedzi i pola (`backend/tests/contract/test_users_profile.py`)
- [X] T039 [P] [US2] Test kontraktowy: `GET /api/v1/users/me/transactions` — paginacja, filtrowanie po typie (`backend/tests/contract/test_users_transactions.py`)
- [X] T040 [P] [US2] Test integracyjny: historia po wielu transakcjach — kolejność, paginacja (`backend/tests/integration/test_transaction_history.py`)
- [X] T041 [P] [US2] Test cache offline: dane wyświetlają się bez sieci przez 24h (`mobile/tests/offlineCache.test.ts`)

### Implementacja US2

- [X] T042 [P] [US2] Schematy Pydantic: odpowiedzi profilu i historii transakcji (`backend/src/schemas/users.py`)
- [X] T043 [US2] Router API: `GET /api/v1/users/me` — profil operacyjny pracownika (`backend/src/api/v1/users.py`)
- [X] T044 [US2] Router API: `GET /api/v1/users/me/transactions` — historia paginowana z filtrowaniem (`backend/src/api/v1/users.py`)
- [X] T045 [P] [US2] Ekran salda: saldo, procent koszyka, data ważności (`mobile/src/screens/BalanceScreen.tsx`)
- [X] T046 [P] [US2] Ekran historii transakcji: lista paginowana (ZAKUP/ZWROT) (`mobile/src/screens/HistoryScreen.tsx`)
- [X] T047 [US2] Logika synchronizacji cache offline: sync przy starcie + wskaźnik „Ostatnia aktualizacja" (`mobile/src/services/sync.ts`)
- [X] T048 [US2] Lokalny store MMKV: `UserSession`, `TransactionHistoryLite` (`mobile/src/store/userStore.ts`)

**Punkt kontrolny**: US1 i US2 działają niezależnie — pracownik widzi saldo i historię

---

## Faza 5: Historia użytkownika 3 — Zabezpieczenia antyszachrajskie i bezpieczeństwo (Priorytet: P3)

**Cel**: Karencja, blokada zerowego salda, ochrona przed wyścigiem, wygasanie, integracja HR, zwroty

**Niezależny test**: Wygeneruj kod przy saldzie 0 (błąd), wyślij dwa jednoczesne żądania POS
dla tego samego kodu (jedno zatwierdzenie), wyślij webhook HR DOŁADOWANIE, zweryfikuj saldo.

### Testy dla US3 — pisać PRZED implementacją ⚠️

- [X] T049 [P] [US3] Test jednostkowy: karencja — blokada gdy `last_code_generated_at` < 30 min temu (`backend/tests/unit/test_cooldown.py`)
- [X] T050 [P] [US3] Test jednostkowy: blokada przy saldzie = 0 PLN (`backend/tests/unit/test_zero_balance_block.py`)
- [X] T051 [P] [US3] Test integracyjny: wyścig procesów — dwa jednoczesne `POST /codes/verify` dla tego samego kodu (`backend/tests/integration/test_race_condition.py`)
- [X] T052 [P] [US3] Test integracyjny: wygasanie kodów — weryfikacja kodu po upływie TTL (`backend/tests/integration/test_code_expiry.py`)
- [X] T053 [P] [US3] Test integracyjny: webhook HR DOŁADOWANIE — saldo zaktualizowane po zdarzeniu (`backend/tests/integration/test_hr_webhook.py`)
- [X] T054 [P] [US3] Test integracyjny: zwrot w oknie 48h i po przekroczeniu okna (`backend/tests/integration/test_refund_window.py`)

### Implementacja US3

- [X] T055 [US3] Rozszerz logikę domenową o walidację karencji 30 min i blokadę zerowego salda (`backend/src/domain/codes.py`)
- [X] T056 [P] [US3] Zadanie cron: wygasanie aktywnych kodów po TTL — zmiana statusu na WYGASŁY (`backend/src/tasks/expire_codes.py`)
- [X] T057 [US3] Serwis domenowy: przetwarzanie zdarzeń HR — NOWY_PRACOWNIK (tworzy rekord + generuje PIN tymczasowy, zwraca go w odpowiedzi webhooka), ZMIANA_KOSZYKA, DOŁADOWANIE, KONIEC_OKRESU (atomowe: zerowanie sald + unieważnienie wszystkich kodów AKTYWNY → WYGASŁY w jednej transakcji), DEZAKTYWACJA, RESET_PIN (generuje nowy PIN tymczasowy, zeruje blokadę); dla wszystkich typów poza NOWY_PRACOWNIK: odrzucenie 422 gdy pracownik nieznany (`backend/src/domain/hr_processor.py`)
- [X] T058 [US3] Serwis domenowy: logika zwrotu — walidacja okna 48h, uznanie rabatu, zapis ZWROT (`backend/src/domain/transactions.py`)
- [X] T059 [P] [US3] Schematy Pydantic: zdarzenia HR i żądanie zwrotu POS (`backend/src/schemas/hr_events.py`)
- [X] T060 [US3] Router API: `POST /api/v1/hr/events` — odbiór i weryfikacja podpisu HMAC-SHA256 (`backend/src/api/v1/hr_events.py`)
- [X] T061 [US3] Router API: `POST /api/v1/codes/refund` — zwrot z walidacją okna 48h (`backend/src/api/v1/codes.py`)
- [X] T062 [P] [US3] Skrypt pomocniczy: generowanie podpisu HMAC do testów webhooka (`backend/scripts/sign_webhook.py`)
- [X] T072 [P] [US3] Test integracyjny: zdarzenie `RESET_PIN` — nowy PIN tymczasowy w odpowiedzi, wymuszona zmiana przy pierwszym logowaniu, zerowanie blokady (`backend/tests/integration/test_reset_pin.py`)
- [X] T073 [P] [US3] Test integracyjny: zdarzenie `KONIEC_OKRESU` — atomowe zerowanie sald + unieważnienie wszystkich kodów AKTYWNY; kod użyty po zdarzeniu → błąd WYGASŁY (`backend/tests/integration/test_period_end_codes.py`)
- [X] T074 [P] [US3] Test integracyjny: webhook z nieznanym `hr_employee_id` → HTTP 422 dla DOŁADOWANIE/ZMIANA_KOSZYKA/RESET_PIN; NOWY_PRACOWNIK → 202 (tworzy rekord) (`backend/tests/integration/test_unknown_employee_webhook.py`)
- [X] T075 [P] [US3] Test jednostkowy: unieważnienie sesji `jti` — stary token 401 po nowym logowaniu tego samego pracownika (`backend/tests/unit/test_jti_invalidation.py`)

**Punkt kontrolny**: Wszystkie trzy historie działają niezależnie i są odporne na nadużycia

---

## Faza N: Szlif i przekrojowe zagadnienia

**Cel**: Retencja danych, audit log, jakość i gotowość produkcyjna

### Retencja danych i audit log (WF-018, KS-009)

- [X] T063 [P] Zadanie cron: usuwanie logów operacyjnych starszych niż 6 miesięcy (generowanie kodów, logowania, blokady) (`backend/src/tasks/purge_logs.py`)
- [X] T064 [P] Zadanie cron: weryfikacja retencji transakcji — alert gdy rekord starszy niż 24 miesiące nie jest zarchiwizowany (`backend/src/tasks/verify_retention.py`)
- [X] T065 [P] Implementacja audit logu operacyjnego: rejestruj generowanie kodów, próby logowania, zdarzenia blokady konta (`backend/src/domain/audit.py`)

### Jakość i gotowość produkcyjna

- [X] T066 [P] Weryfikacja i uzupełnienie dokumentacji OpenAPI (opisy, przykłady, kody błędów dla auth) (`backend/src/main.py`)
- [X] T067 Walidacja quickstart.md — przebieg end-to-end z logowaniem PIN zgodnie z dokumentem (`specs/001-bonus-app/quickstart.md`)
- [X] T068 [P] Konfiguracja Docker Compose gotowa do produkcji: healthchecks, zmienne env, sekrety (`docker-compose.yml`)
- [X] T069 [P] Dodatkowe testy jednostkowe: wygasła data ważności środków, dezaktywowany pracownik, wygasły JWT (`backend/tests/unit/`)
- [X] T070 [P] Przegląd i refaktoryzacja kodu po zakończeniu wszystkich historii
- [X] T071 [P] Weryfikacja bezpieczeństwa: TLS, brak wycieku szczegółów błędów, bezpieczne przechowywanie JWT w MMKV (`backend/src/`, `mobile/src/`)

---

## Zależności i kolejność wykonania

### Zależności faz

- **Faza 1 (Konfiguracja)**: Brak zależności — można zacząć natychmiast
- **Faza 2 (Fundament)**: Zależy od Fazy 1 — **BLOKUJE wszystkie historie**; zawiera logowanie
- **Faza 3 (US1)**: Zależy od Fazy 2 — 🎯 MVP po ukończeniu
- **Faza 4 (US2)**: Zależy od Fazy 2; może być równolegle z US1 przy osobnych deweloperach
- **Faza 5 (US3)**: Zależy od Fazy 2; rozszerza `codes.py` i `transactions.py` z US1
- **Faza N (Szlif)**: Zależy od ukończenia wybranych historii

### Zależności wewnątrz Fazy 2 (auth)

```
T007 (model User z polami auth)
  → T010 (migracje Alembic)
  → T014 (serwis domenowy auth)    # zależy od modelu
    → T015 (router /auth/login)    # zależy od serwisu
    → T018 (deps.py JWT)           # zależy od serwisu (weryfikacja tokenów)
T011 (schematy auth) ← T015       # schematy przed routerem
T012, T013 (testy auth) — pisać przed T014
T016 (LoginScreen) ← T036 (api.ts mobile) # ekran przed klientem API
```

### Zależności wewnątrz US1

```
T029 (generowanie kodu)
  → T030 (weryfikacja kodu)      # ta sama klasa domenowa
    → T031 (finalizacja)         # zależy od zweryfikowanego kodu
      → T032 (router /codes)
      → T033 (router /verify)
      → T034 (router /finalize)
T035 (CodeDisplayScreen) ← T036 (api.ts)
```

### Zależności wewnątrz US3

```
T055 (rozszerzenie codes.py)     # zależy od T029-T030 z US1
T057 (hr_processor)              # niezależny od US1
T058 (logika zwrotu)             # zależy od T031 z US1
T060 (router hr/events)          # zależy od T057
T061 (router /refund)            # zależy od T058
```

### Możliwości równoległe

- Faza 1: T002, T003, T004, T005 — równolegle
- Faza 2 (modele): T007 + T008 — równolegle; T010 po obu
- Faza 2 (auth): T011, T012, T013 — równolegle (przed T014)
- Faza 2 (middleware): T018, T019, T020 — równolegle
- Testy każdej historii: wszystkie równolegle przed implementacją
- US2 i US3: można równolegle po Fazie 2 (różni deweloperzy)

---

## Przykład równoległego wykonania — Faza 2 (auth)

```bash
# Równolegle — pisz testy przed implementacją:
Zadanie: "Schematy Pydantic auth" (T011)
Zadanie: "Test jednostkowy PIN lockout" (T012)
Zadanie: "Test integracyjny auth flow" (T013)

# Po czerwonych testach — implementacja:
Zadanie: "Serwis domenowy auth" (T014)
# Następnie:
Zadanie: "Router /auth/login" (T015)
Zadanie: "deps.py JWT" (T018)

# Równolegle — mobile:
Zadanie: "LoginScreen" (T016)
Zadanie: "Test LoginScreen" (T017)
```

---

## Strategia implementacji

### MVP Najpierw (US1 + logowanie)

1. Ukończ Fazę 1: Konfiguracja
2. Ukończ Fazę 2: Fundament — w tym logowanie PIN (T007–T021)
3. Napisz testy US1 (T022–T027) i upewnij się, że CZERWIEJĄ
4. Ukończ Fazę 3: US1
5. **ZATRZYMAJ I ZWALIDUJ**: Zaloguj się → wygeneruj kod → zakup przy kasie
6. Demonstracja MVP

### Dostawa inkrementalna

1. Faza 1 + Faza 2 → Fundament z logowaniem
2. US1 → Przetestuj niezależnie → MVP
3. US2 → Przetestuj niezależnie (saldo + offline)
4. US3 → Przetestuj niezależnie (zabezpieczenia + HR + zwroty)
5. Faza N → Retencja danych, audit log, gotowość produkcyjna

### Strategia równoległego zespołu

Po ukończeniu Fazy 2:

- Deweloper A: US1 (backend: codes.py, transactions.py, router + mobile: CodeDisplayScreen)
- Deweloper B: US2 (backend: users.py + mobile: BalanceScreen, HistoryScreen, sync)
- Po US1+US2: US3 razem (zabezpieczenia, HR, zwroty)
- Faza N równolegle z US3: T063–T065 (retencja + audit log)

---

## Uwagi

- `[P]` = różne pliki, brak zależności — można uruchamiać równolegle
- `[US]` mapuje zadanie do konkretnej historii użytkownika dla śledzenia
- Testy MUSZĄ być napisane i CZERWONE przed implementacją (Konstytucja Zasada III)
- Commity po każdym zadaniu lub logicznej grupie
- Zatrzymaj się na każdym punkcie kontrolnym, aby zwalidować historię niezależnie
- JWT przechowywany w MMKV (mobile) — nigdy w niezabezpieczonym AsyncStorage
