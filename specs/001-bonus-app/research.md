# Badania: BonusApp — Subsystem benefitów pracowniczych

**Wejście**: Specyfikacja `spec.md` + Konstytucja Piekarnia v1.0.0
**Data**: 2026-04-10

---

## 1. Frontend — aplikacja mobilna vs. webowa

**Decyzja**: React Native (iOS + Android) jako aplikacja mobilna.

**Uzasadnienie**: Pracownicy korzystają z systemu stojąc przy kasie, często w ruchu i bez
dostępu do laptopa. Aplikacja mobilna umożliwia szybkie generowanie kodu jednym gestem.
Wymóg buforowania offline (KS-007) jest naturalnie realizowany przez lokalne magazyny
React Native (AsyncStorage / MMKV). React Native pozwala współdzielić kod logiki biznesowej
między iOS a Androidem przy jednej bazie kodu TypeScript.

**Alternatywy rozważone**:
- PWA (Progressive Web App) — odrzucona; ograniczona obsługa offline na iOS Safari,
  gorsza integracja z aparatem do skanowania kodów QR.
- Natywny iOS/Android — odrzucona; wymaga dwóch oddzielnych baz kodu i zespołów.

---

## 2. Format i generowanie kodów OTP

**Decyzja**: Kod 6-cyfrowy (numeryczny), generowany kryptograficznie po stronie serwera,
przechowywany jako hash (bcrypt) w tabeli `auth_codes`.

**Uzasadnienie**: 6 cyfr to standard w branży (TOTP/mTAN). Kasjer może łatwo wpisać je
ręcznie przy braku skanera. Liczba możliwych kodów (10^6) przy TTL 15 min i karencji 30 min
daje margines bezpieczeństwa wystarczający dla małej/średniej sieci placówek (< 10k pracowników).
Przechowywanie hashu zamiast wartości surowej chroni przed kompromitacją bazy.

**Alternatywy rozważone**:
- UUID/token alfanumeryczny — odrzucona; trudny do wpisania ręcznie przez kasjera.
- TOTP (RFC 6238) — odrzucona; wymaga synchronizacji zegara między urządzeniami i serwera;
  nadmiarowa złożoność dla jednorazowego użycia.

---

## 3. Obsługa wyścigu procesów przy weryfikacji kodu (POS)

**Decyzja**: Pesymistyczne blokowanie wiersza (`SELECT ... FOR UPDATE`) w transakcji bazy danych
podczas weryfikacji kodu przez POS.

**Uzasadnienie**: Wymóg KS-006 (0% podwójnych rabatów) wymaga gwarancji na poziomie bazy.
Pesymistyczne blokowanie jest prostsze w implementacji niż optymistyczna wersjonowanie i
eliminuje wyścig przy jednoczesnych żądaniach POS dla tego samego kodu.

**Alternatywy rozważone**:
- Optymistyczne blokowanie (version field) — odrzucona; wymaga retry logic po stronie klienta
  POS i zwiększa złożoność protokołu.
- Redis distributed lock — odrzucona; dodaje zewnętrzną zależność; PostgreSQL wystarczy.

---

## 4. Integracja z systemem kadrowo-płacowym (HR)

**Decyzja**: Webhook inbound — system HR wysyła zdarzenia HTTP POST do API BonusApp
przy zmianach: nowy pracownik, zmiana koszyka, doładowanie salda, koniec okresu.

**Uzasadnienie**: Podejście event-driven minimalizuje opóźnienie synchronizacji danych.
BonusApp nie musi aktywnie odpytywać systemu HR (polling), co upraszcza harmonogram
i zmniejsza obciążenie obu systemów. API BonusApp weryfikuje podpis HMAC każdego webhooka.

**Alternatywy rozważone**:
- Polling co N minut — odrzucona; opóźniona synchronizacja może skutkować zatwierdzeniem
  kodu pracownika, który właśnie stracił uprawnienia.
- Bezpośrednie wywołanie API HR przy każdym żądaniu — odrzucona; silne sprzężenie,
  awaria HR blokuje BonusApp.

---

## 5. Protokół integracji POS

**Decyzja**: REST/HTTP z uwierzytelnianiem przez klucz API (per-terminal API key)
przekazywany w nagłówku `X-POS-API-Key`. TLS obowiązkowy. Timeout żądania POS: 5 s.

**Uzasadnienie**: Systemy POS typowo obsługują wywołania HTTP REST. Klucze API per-terminal
pozwalają na selektywne unieważnienie skompromitowanego terminala bez wpływu na inne.
Cel KS-002 (< 3 s odpowiedzi) jest objęty timeoutem 5 s (margines na sieć wewnętrzną).

**Alternatywy rozważone**:
- OAuth2 client credentials — odrzucona; nadmiarowe dla urządzeń terminalowych bez
  przeglądarki; zarządzanie tokenami komplikuje integrację POS.
- mTLS — rozważone jako przyszłe wzmocnienie; nie blokuje MVP.

---

## 6. Strategia buforowania offline w aplikacji mobilnej

**Decyzja**: Lokalny magazyn (AsyncStorage lub MMKV) przechowuje `UserSession`
(profil, saldo, koszyk, data ważności) i `TransactionHistoryLite` (ostatnie N transakcji).
Synchronizacja przy każdym otwarciu aplikacji gdy sieć dostępna.

**Uzasadnienie**: Spełnia wymóg KS-007 (24 h bez sieci). Dane są wyłącznie do odczytu
(nie służą do autoryzacji), więc brak ryzyka desynchronizacji finansowej.
`ActiveToken` (lokalnie buforowany kod) NIE jest przechowywany — kody generowane wyłącznie online.

**Alternatywy rozważone**:
- SQLite lokalnie — rozważone; nadmiarowe dla ilości danych (profil + historia);
  AsyncStorage/MMKV wystarczy dla płaskich struktur JSON.

---

## 7. Stos technologiczny (potwierdzony)

| Komponent | Technologia | Wersja |
|-----------|-------------|--------|
| Backend API | Python + FastAPI | Python 3.12, FastAPI 0.111+ |
| Baza danych | PostgreSQL | 16+ |
| ORM | SQLAlchemy | 2.x (async) |
| Migracje | Alembic | najnowsza |
| Testy backend | pytest + pytest-asyncio | najnowsza |
| Testy kontraktowe | Schemathesis (OpenAPI fuzz) | najnowsza |
| Frontend mobile | React Native | 0.74+ |
| Testy frontend | Jest + React Native Testing Library | najnowsza |
| Konteneryzacja | Docker + Docker Compose | — |
| Dokumentacja API | OpenAPI 3.1 (generowana przez FastAPI) | — |
