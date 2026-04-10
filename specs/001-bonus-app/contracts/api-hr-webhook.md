# Kontrakt API: Webhook integracji HR

**Wersja**: 1.0.0 | **Data**: 2026-04-10
**Podstawa**: `spec.md` WF-011, `research.md` §4

---

## Uwierzytelnianie

System HR podpisuje każde żądanie podpisem HMAC-SHA256 w nagłówku `X-HR-Signature`.
BonusApp weryfikuje podpis przed przetworzeniem zdarzenia.

```
X-HR-Signature: sha256=<hex_digest>
Content-Type: application/json
```

---

## POST /api/v1/hr/events

Odbiera zdarzenie z systemu kadrowo-płacowego.

### Typy zdarzeń

#### NOWY_PRACOWNIK

```json
{
  "event_type": "NOWY_PRACOWNIK",
  "event_id": "hr-evt-0001",
  "occurred_at": "2026-04-01T08:00:00Z",
  "payload": {
    "hr_employee_id": "EMP-00422",
    "basket_id": "BASKET-KASOWI",
    "location_id": "PLK-WARSZAWA-001",
    "initial_balance_pln": "150.00",
    "balance_expiry_date": "2026-04-30"
  }
}
```

#### ZMIANA_KOSZYKA

```json
{
  "event_type": "ZMIANA_KOSZYKA",
  "event_id": "hr-evt-0002",
  "occurred_at": "2026-04-10T00:00:00Z",
  "payload": {
    "hr_employee_id": "EMP-00421",
    "new_basket_id": "BASKET-KIEROWNICY",
    "effective_from": "2026-04-10"
  }
}
```

#### DOŁADOWANIE

```json
{
  "event_type": "DOŁADOWANIE",
  "event_id": "hr-evt-0003",
  "occurred_at": "2026-04-01T00:00:00Z",
  "payload": {
    "hr_employee_id": "EMP-00421",
    "amount_pln": "200.00",
    "balance_expiry_date": "2026-04-30"
  }
}
```

#### KONIEC_OKRESU

```json
{
  "event_type": "KONIEC_OKRESU",
  "event_id": "hr-evt-0004",
  "occurred_at": "2026-03-31T23:59:59Z",
  "payload": {
    "period_end_date": "2026-03-31",
    "affected_employee_count": 145
  }
}
```

Zeruje salda wszystkich aktywnych pracowników, których `balance_expiry_date` ≤ `period_end_date`.

#### DEZAKTYWACJA

```json
{
  "event_type": "DEZAKTYWACJA",
  "event_id": "hr-evt-0005",
  "occurred_at": "2026-04-10T12:00:00Z",
  "payload": {
    "hr_employee_id": "EMP-00399",
    "reason": "ROZWIĄZANIE_UMOWY"
  }
}
```

### Odpowiedzi

**202 Accepted** — zdarzenie przyjęte do kolejki (przetwarzane asynchronicznie)

```json
{
  "status": "PRZYJĘTE",
  "event_id": "hr-evt-0001"
}
```

**400 Bad Request** — nieznany typ zdarzenia lub brakujące pola

```json
{
  "error": "NIEPRAWIDŁOWE_ZDARZENIE",
  "message": "Pole payload.hr_employee_id jest wymagane."
}
```

**401 Unauthorized** — nieważny podpis HMAC

```json
{
  "error": "NIEWAŻNY_PODPIS",
  "message": "Podpis X-HR-Signature jest nieprawidłowy."
}
```

**409 Conflict** — duplikat `event_id` (idempotencja)

```json
{
  "status": "PRZYJĘTE",
  "event_id": "hr-evt-0001",
  "message": "Zdarzenie zostało już zarejestrowane."
}
```

---

## Kontrakt zwrotu POS

### POST /api/v1/codes/refund

Inicjuje zwrot rabatu dla wcześniejszej transakcji. Wywoływany przez POS przy zwrocie towaru.

**Uwierzytelnianie**: `X-POS-API-Key`

### Żądanie

```json
{
  "original_transaction_id": "txn_9f3a2b1c",
  "pos_refund_ref": "POS-REF-20260410-0007",
  "gross_refund_amount_pln": "85.00"
}
```

### Odpowiedzi

**200 OK** — zwrot zatwierdzony

```json
{
  "status": "ZWROT_ZATWIERDZONY",
  "refund_transaction_id": "txn_r1a2b3c4",
  "credited_amount_pln": "8.50",
  "balance_after_pln": "135.50"
}
```

**422 Unprocessable Entity** — upłynął czas okna zwrotu (> 48 h)

```json
{
  "error": "OKNO_ZWROTU_UPŁYNĘŁO",
  "message": "Zwrot automatyczny możliwy tylko w ciągu 48 godzin od transakcji. Skontaktuj się z działem HR.",
  "original_created_at": "2026-04-08T10:00:00Z",
  "window_closed_at": "2026-04-10T10:00:00Z"
}
```

**404 Not Found** — nieznana transakcja oryginalna

```json
{
  "error": "TRANSAKCJA_NIE_ZNALEZIONA",
  "message": "Transakcja o podanym ID nie istnieje lub nie należy do tego terminala."
}
```
