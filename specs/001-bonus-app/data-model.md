# Model danych: BonusApp — Subsystem benefitów pracowniczych

**Wejście**: `spec.md` + `research.md`
**Data**: 2026-04-10

---

## Encje i pola

### Użytkownik (`users`)

Reprezentuje pracownika posiadającego konto w systemie BonusApp.
Dane masterowe (imię, nazwisko, nr pracownika) pochodzą z systemu HR i nie są
powielane — encja przechowuje wyłącznie dane finansowo-operacyjne.

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| `id` | UUID | PK, not null | Wewnętrzny identyfikator |
| `hr_employee_id` | VARCHAR(64) | UNIQUE, not null | ID pracownika w systemie HR |
| `basket_id` | UUID | FK → baskets, not null | Przypisany koszyk rabatowy |
| `pin_hash` | VARCHAR(128) | not null | Hash bcrypt PIN-u (4–6 cyfr) |
| `must_change_pin` | BOOLEAN | not null, default false | Wymuszenie zmiany PIN przy następnym logowaniu |
| `login_attempts` | SMALLINT | not null, default 0 | Liczba nieudanych prób logowania |
| `locked_until` | TIMESTAMPTZ | nullable | Blokada konta do podanego czasu (null = brak blokady) |
| `current_jti` | UUID | nullable | JTI aktywnego tokenu JWT (null = brak aktywnej sesji) |
| `current_balance` | NUMERIC(10,2) | not null, ≥ 0 | Aktualne saldo w PLN |
| `balance_expiry_date` | DATE | not null | Data wygaśnięcia bieżących środków |
| `last_code_generated_at` | TIMESTAMPTZ | nullable | Znacznik ostatniego generowania kodu |
| `is_active` | BOOLEAN | not null, default true | Czy pracownik uprawniony (soft-disable) |
| `location_id` | VARCHAR(64) | not null | ID placówki fizycznej (z systemu HR) |
| `created_at` | TIMESTAMPTZ | not null, default now() | Data utworzenia rekordu |
| `updated_at` | TIMESTAMPTZ | not null, default now() | Data ostatniej aktualizacji |

**Reguły walidacji**:
- `current_balance` ≥ 0 — wymuszane na poziomie bazy (CHECK constraint).
- `balance_expiry_date` musi być datą przyszłą lub bieżącą przy doładowaniu.
- Tylko jeden aktywny koszyk (`basket_id`) na pracownika w danym momencie.
- `login_attempts` ≥ 5 → konto zablokowane przez 15 min (`locked_until = now() + 15 min`); licznik zerowany po udanym logowaniu.
- `must_change_pin = true` ustawiany przy onboardingu (NOWY_PRACOWNIK) i resecie PIN (RESET_PIN); zerowany po pomyślnej zmianie PIN.
- `current_jti` aktualizowany przy każdym logowaniu; middleware odrzuca token z niezgodnym `jti` (HTTP 401).

**Przejścia stanu**:
- `is_active: true → false`: pracownik odchodzi z firmy lub traci uprawnienia (zdarzenie HR DEZAKTYWACJA).
- `must_change_pin: false → true`: przy zdarzeniu NOWY_PRACOWNIK lub RESET_PIN.
- `must_change_pin: true → false`: po pomyślnym wywołaniu `/auth/change-pin`.
- Saldo zerowane atomowo przy zdarzeniu KONIEC_OKRESU (jednocześnie unieważniane wszystkie kody AKTYWNY).

---

### Koszyk (`baskets`)

Reprezentuje grupę rabatową — zbiór pracowników ze wspólnym procentem rabatu i limitem.

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| `id` | UUID | PK, not null | Wewnętrzny identyfikator |
| `hr_basket_id` | VARCHAR(64) | UNIQUE, not null | ID koszyka w systemie HR |
| `name` | VARCHAR(128) | not null | Nazwa grupy (np. „Pracownicy kasowi") |
| `discount_pct` | NUMERIC(5,2) | not null, 0 < x ≤ 100 | Procent rabatu |
| `monthly_limit_pln` | NUMERIC(10,2) | nullable | Miesięczny limit rabatu w PLN (null = brak) |
| `is_active` | BOOLEAN | not null, default true | Czy koszyk aktywny |
| `created_at` | TIMESTAMPTZ | not null, default now() | Data utworzenia |
| `updated_at` | TIMESTAMPTZ | not null, default now() | Data aktualizacji |

**Reguły walidacji**:
- `discount_pct` musi być > 0 i ≤ 100.
- Usunięcie koszyka niedozwolone gdy ma przypisanych aktywnych użytkowników — soft-delete.

---

### Kod autoryzacyjny (`auth_codes`)

Jednorazowy OTP generowany dla pracownika do użycia przy kasie.

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| `id` | UUID | PK, not null | Wewnętrzny identyfikator |
| `user_id` | UUID | FK → users, not null | Właściciel kodu |
| `code_hash` | VARCHAR(128) | not null | Hash bcrypt 6-cyfrowego kodu |
| `status` | ENUM | not null | AKTYWNY / WYKORZYSTANY / WYGASŁY |
| `created_at` | TIMESTAMPTZ | not null, default now() | Czas generowania |
| `expires_at` | TIMESTAMPTZ | not null | `created_at + 15 min` |
| `used_at` | TIMESTAMPTZ | nullable | Czas użycia (przy finalizacji POS) |
| `transaction_id` | UUID | FK → transactions, nullable | Powiązana transakcja (po finalizacji) |

**Przejścia stanu**:
```
AKTYWNY → WYKORZYSTANY  : po pomyślnej finalizacji POS
AKTYWNY → WYGASŁY       : po upływie expires_at (zadanie cron lub przy weryfikacji)
```

**Reguły walidacji**:
- Tylko jeden kod w statusie AKTYWNY per pracownik w danym momencie.
- Nowy kod nie może być wygenerowany jeśli `last_code_generated_at` < 30 min temu.
- Surowa wartość kodu nie jest nigdy przechowywana — tylko hash.

---

### Transakcja (`transactions`)

Niezmienialny snapshot zakupu lub zwrotu. Odzwierciedla stan rabatu w momencie transakcji.

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| `id` | UUID | PK, not null | Wewnętrzny identyfikator |
| `user_id` | UUID | FK → users, not null | Pracownik |
| `code_id` | UUID | FK → auth_codes, not null | Użyty kod autoryzacyjny |
| `pos_terminal_id` | VARCHAR(64) | not null | ID terminala POS |
| `pos_transaction_ref` | VARCHAR(128) | nullable | Referencja transakcji z systemu POS |
| `type` | ENUM | not null | ZAKUP / ZWROT |
| `gross_amount_pln` | NUMERIC(10,2) | not null, > 0 | Wartość brutto zakupu |
| `discount_pct_snapshot` | NUMERIC(5,2) | not null | Procent rabatu zamrożony w momencie transakcji |
| `discount_amount_pln` | NUMERIC(10,2) | not null, ≥ 0 | Kwota rabatu zastosowanego |
| `net_amount_pln` | NUMERIC(10,2) | not null | `gross_amount - discount_amount` |
| `basket_snapshot_id` | UUID | FK → baskets, not null | Koszyk w momencie transakcji |
| `balance_before_pln` | NUMERIC(10,2) | not null | Saldo przed transakcją (audit) |
| `balance_after_pln` | NUMERIC(10,2) | not null | Saldo po transakcji (audit) |
| `original_transaction_id` | UUID | FK → transactions, nullable | Dla ZWROT: referencja do oryginalnego ZAKUPU |
| `created_at` | TIMESTAMPTZ | not null, default now() | Czas finalizacji |

**Reguły walidacji**:
- Rekord jest IMMUTABLE po utworzeniu — brak UPDATE, tylko INSERT.
- Dla ZWROT: `original_transaction_id` MUSI być podany i wskazywać na ZAKUP tego samego pracownika.
- Zwrot możliwy tylko jeśli `created_at` oryginału ≥ now() - okno_zwrotu (domyślnie 48 h).
- `discount_amount_pln` = `min(balance_before, floor(gross_amount × discount_pct_snapshot / 100))`.

---

### Zdarzenie HR (`hr_events`) — tabela robocza

Kolejka przychodzących webhooków z systemu HR do przetworzenia asynchronicznie.

| Pole | Typ | Ograniczenia | Opis |
|------|-----|-------------|------|
| `id` | UUID | PK, not null | Identyfikator zdarzenia |
| `event_type` | ENUM | not null | NOWY_PRACOWNIK / ZMIANA_KOSZYKA / DOŁADOWANIE / KONIEC_OKRESU / DEZAKTYWACJA / RESET_PIN |
| `payload` | JSONB | not null | Surowe dane zdarzenia z systemu HR |
| `status` | ENUM | not null, default OCZEKUJĄCE | OCZEKUJĄCE / PRZETWORZONE / BŁĄD |
| `received_at` | TIMESTAMPTZ | not null, default now() | Czas odebrania webhooka |
| `processed_at` | TIMESTAMPTZ | nullable | Czas przetworzenia |
| `error_message` | TEXT | nullable | Opis błędu (jeśli status = BŁĄD) |

---

## Diagram relacji (uproszczony)

```
baskets ──< users ──< auth_codes ──< transactions
                 └──────────────────────────────┘
                 (user_id w transactions)

transactions >── transactions
(original_transaction_id dla zwrotów)

hr_events (niezależna tabela robocza — brak FK do innych encji)
```

---

## Uwagi implementacyjne

- Wszystkie operacje modyfikujące saldo (`current_balance`) MUSZĄ być wykonywane
  w transakcji bazodanowej z blokadą wiersza (`SELECT ... FOR UPDATE` na `users`).
- Indeksy: `auth_codes(user_id, status)`, `auth_codes(expires_at)` (cron wygasania),
  `transactions(user_id, created_at DESC)` (historia paginowana),
  `hr_events(status, received_at)` (kolejka).
- Soft-delete dla `users` i `baskets` (pole `is_active`) — twarde usuwanie zabronione.
