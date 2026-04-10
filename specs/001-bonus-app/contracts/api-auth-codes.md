# Kontrakt API: Kody autoryzacyjne (generowanie i weryfikacja)

**Wersja**: 1.0.0 | **Data**: 2026-04-10
**Podstawa**: `spec.md` WF-001–WF-003, WF-009–WF-010

---

## Uwierzytelnianie

- **Aplikacja mobilna → API**: Bearer token JWT (sesja zalogowanego pracownika).
- **POS → API**: Klucz API terminala w nagłówku `X-POS-API-Key`.
- Wszystkie połączenia MUSZĄ używać TLS.

---

## POST /api/v1/codes

Generuje jednorazowy kod autoryzacyjny dla zalogowanego pracownika.

**Wywołujący**: Aplikacja mobilna pracownika.

### Żądanie

```
POST /api/v1/codes
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

Brak body — kod generowany na podstawie tożsamości z tokenu JWT.

### Odpowiedzi

**200 OK** — kod wygenerowany pomyślnie

```json
{
  "code": "482931",
  "expires_at": "2026-04-10T14:32:00Z",
  "balance_pln": "127.50",
  "basket_discount_pct": "10.00"
}
```

**409 Conflict** — aktywna karencja

```json
{
  "error": "AKTYWNA_KARENCJA",
  "message": "Kolejny kod można wygenerować za 18 minut.",
  "retry_after_seconds": 1080
}
```

**422 Unprocessable Entity** — zerowe saldo

```json
{
  "error": "ZEROWE_SALDO",
  "message": "Saldo wynosi 0 PLN. Generowanie kodu jest niedostępne."
}
```

**401 Unauthorized** — nieważny lub wygasły token JWT

```json
{
  "error": "NIEAUTORYZOWANY",
  "message": "Token sesji jest nieważny lub wygasł."
}
```

---

## POST /api/v1/codes/verify

Weryfikuje kod przy kasie i oblicza kwotę rabatu. Wywoływane przez POS **przed** finalizacją.

**Wywołujący**: Terminal POS.

### Żądanie

```
POST /api/v1/codes/verify
X-POS-API-Key: <terminal_api_key>
Content-Type: application/json
```

```json
{
  "code": "482931",
  "pos_transaction_ref": "POS-TXN-20260410-0042",
  "gross_amount_pln": "85.00"
}
```

| Pole | Typ | Wymagane | Opis |
|------|-----|----------|------|
| `code` | string(6) | tak | Wprowadzony/zeskanowany kod |
| `pos_transaction_ref` | string | tak | Referencja transakcji POS (idempotencja) |
| `gross_amount_pln` | string (decimal) | tak | Wartość brutto zakupu w PLN |

### Odpowiedzi

**200 OK** — kod ważny, rabat zatwierdzony

```json
{
  "status": "ZATWIERDZONE",
  "verification_token": "eyJhbGci...",
  "discount_amount_pln": "8.50",
  "net_amount_pln": "76.50",
  "user_display_name": "Jan K.",
  "expires_at": "2026-04-10T14:32:00Z"
}
```

Pole `verification_token` jest wymagane do wywołania `/codes/finalize`.

**409 Conflict** — kod już wykorzystany

```json
{
  "error": "JUŻ_WYKORZYSTANY",
  "message": "Kod został już użyty przy poprzedniej transakcji."
}
```

**410 Gone** — kod wygasł

```json
{
  "error": "WYGASŁY",
  "message": "Kod wygasł. Pracownik musi wygenerować nowy kod."
}
```

**422 Unprocessable Entity** — niewystarczające saldo

```json
{
  "error": "NIEWYSTARCZAJĄCE_SALDO",
  "message": "Saldo pracownika jest niewystarczające do realizacji transakcji.",
  "current_balance_pln": "3.20"
}
```

**404 Not Found** — nieznany kod

```json
{
  "error": "NIEZNANY_KOD",
  "message": "Podany kod nie istnieje."
}
```

---

## POST /api/v1/codes/finalize

Finalizuje transakcję po stronie API: oznacza kod jako WYKORZYSTANY, tworzy Transakcję,
aktualizuje saldo. Wywoływane przez POS **po** pomyślnym zakończeniu sprzedaży.

**Wywołujący**: Terminal POS.

### Żądanie

```
POST /api/v1/codes/finalize
X-POS-API-Key: <terminal_api_key>
Content-Type: application/json
```

```json
{
  "verification_token": "eyJhbGci...",
  "pos_transaction_ref": "POS-TXN-20260410-0042"
}
```

### Odpowiedzi

**200 OK** — finalizacja pomyślna

```json
{
  "status": "SFINALIZOWANE",
  "transaction_id": "txn_9f3a2b1c",
  "balance_after_pln": "119.00"
}
```

**409 Conflict** — duplikat (idempotencja po `pos_transaction_ref`)

```json
{
  "status": "SFINALIZOWANE",
  "transaction_id": "txn_9f3a2b1c",
  "message": "Transakcja już zarejestrowana."
}
```

**401 Unauthorized** — nieważny lub wygasły `verification_token`

```json
{
  "error": "NIEWAŻNY_TOKEN_WERYFIKACJI",
  "message": "Token weryfikacji jest nieważny lub wygasł."
}
```
