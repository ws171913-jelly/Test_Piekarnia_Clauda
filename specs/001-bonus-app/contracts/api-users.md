# Kontrakt API: Użytkownicy — saldo i historia

**Wersja**: 1.0.0 | **Data**: 2026-04-10
**Podstawa**: `spec.md` WF-007–WF-008, Historia użytkownika 2

---

## Uwierzytelnianie

Wszystkie endpointy wymagają `Authorization: Bearer <jwt_token>` (sesja pracownika).

---

## GET /api/v1/users/me

Zwraca profil operacyjny zalogowanego pracownika: saldo, koszyk, datę ważności.

### Odpowiedź — 200 OK

```json
{
  "hr_employee_id": "EMP-00421",
  "current_balance_pln": "127.50",
  "balance_expiry_date": "2026-04-30",
  "basket": {
    "name": "Pracownicy kasowi",
    "discount_pct": "10.00",
    "monthly_limit_pln": "200.00"
  },
  "location_id": "PLK-WARSZAWA-001",
  "last_synced_at": "2026-04-10T12:00:00Z"
}
```

---

## GET /api/v1/users/me/transactions

Zwraca stronicowaną historię transakcji zalogowanego pracownika.

### Parametry zapytania

| Parametr | Typ | Domyślna | Opis |
|----------|-----|---------|------|
| `page` | int | 1 | Numer strony (1-based) |
| `page_size` | int | 20 | Rozmiar strony (max 100) |
| `type` | string | brak | Filtr: `ZAKUP` lub `ZWROT` |

### Odpowiedź — 200 OK

```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "txn_9f3a2b1c",
      "type": "ZAKUP",
      "gross_amount_pln": "85.00",
      "discount_amount_pln": "8.50",
      "net_amount_pln": "76.50",
      "discount_pct_snapshot": "10.00",
      "pos_terminal_id": "POS-WA-003",
      "created_at": "2026-04-10T13:45:00Z"
    },
    {
      "id": "txn_1a2b3c4d",
      "type": "ZWROT",
      "gross_amount_pln": "30.00",
      "discount_amount_pln": "3.00",
      "net_amount_pln": "27.00",
      "discount_pct_snapshot": "10.00",
      "pos_terminal_id": "POS-WA-003",
      "original_transaction_id": "txn_0a1b2c3d",
      "created_at": "2026-04-09T10:20:00Z"
    }
  ]
}
```
