# Specyfikacja funkcjonalna: BonusApp — Subsystem benefitów pracowniczych

**Gałąź funkcjonalności**: `001-bonus-app`
**Utworzono**: 2026-04-10
**Status**: Szkic
**Wejście**: Opis użytkownika: subsystem benefitów pracowniczych umożliwiający pracownikom korzystanie ze środków bonusowych przy zakupach w placówkach pracodawcy

## Scenariusze użytkownika i testowanie *(wymagane)*

### Historia użytkownika 1 — Przebieg zakupu z rabatem (Priorytet: P1)

Pracownik otwiera aplikację mobilną, generuje jednorazowy kod rabatowy i przedstawia go przy
kasie. Kasjer wprowadza lub skanuje kod; system POS kontaktuje się z API, które potwierdza
uprawnienia pracownika i dostępne saldo, a następnie zwraca zatwierdzoną kwotę rabatu.
Po sfinalizowaniu sprzedaży przez POS, API rejestruje transakcję i potrąca rabat z salda pracownika.

**Dlaczego ten priorytet**: To jest główny cel istnienia systemu. Bez kompletnego przebiegu
zakupu żadna inna historia nie dostarcza wartości.

**Niezależny test**: Można w pełni przetestować poprzez wygenerowanie kodu przez pracownika,
przesłanie go przez klienta POS z wartością transakcji i weryfikację, że API zwraca zatwierdzenie,
saldo zostaje pomniejszone, a rekord transakcji zostaje utworzony — bez żadnego interfejsu
poza minimalnym szkieletem mobilnym.

**Scenariusze akceptacyjne**:

1. **Mając** pracownika z saldem 200 PLN i przypisaniem do koszyka 10%,
   **gdy** generuje kod, a kasjer przesyła go z wartością zakupu 100 PLN,
   **to** API zwraca `zatwierdzone`, `kwota_rabatu = 10 PLN`, a po sfinalizowaniu przez POS
   saldo pracownika wynosi 190 PLN z nowym rekordem Transakcji.

2. **Mając** pracownika z saldem 5 PLN i koszyk 10%,
   **gdy** kasjer przesyła kod z wartością zakupu 200 PLN (potencjalny rabat = 20 PLN),
   **to** API zwraca błąd salda i transakcja jest odrzucona.

3. **Mając** kod pracownika wygenerowany 16 minut temu (TTL = 15 min),
   **gdy** kasjer przesyła go do POS,
   **to** API zwraca błąd `WYGASŁY` i transakcja jest odrzucona.

4. **Mając** kod pracownika ze statusem `WYKORZYSTANY`,
   **gdy** kasjer przesyła go po raz drugi,
   **to** API zwraca błąd `JUŻ_WYKORZYSTANY`.

---

### Historia użytkownika 2 — Podgląd salda i historii transakcji (Priorytet: P2)

Pracownik otwiera aplikację, aby sprawdzić aktualne saldo bonusowe, poziom rabatu (koszyk),
datę ważności środków oraz listę minionych transakcji — z kwotami, datami i zastosowanymi
rabatami. Nawet w trybie offline aplikacja wyświetla dane z ostatniej udanej synchronizacji.

**Dlaczego ten priorytet**: Przejrzystość finansowa buduje zaufanie pracowników. Ta historia
jest niezależnie użyteczna nawet jeśli historia 1 jest realizowana przez inny zespół.

**Niezależny test**: Można przetestować przez załadowanie aplikacji, porównanie wyświetlanych
danych z saldami i historią ze stanu bazy, odłączenie sieci i weryfikację, że dane z pamięci
podręcznej pozostają widoczne.

**Scenariusze akceptacyjne**:

1. **Mając** pracownika z saldem 150 PLN i trzema przeszłymi transakcjami,
   **gdy** otwiera ekran salda,
   **to** aplikacja wyświetla aktualne saldo, procent rabatu koszyka, datę ważności środków
   oraz wszystkie trzy transakcje z poprawnymi kwotami i datami.

2. **Mając** pracownika, którego urządzenie nie ma łączności z siecią,
   **gdy** otwiera ekran salda,
   **to** aplikacja wyświetla ostatnio zbuforowane saldo i listę transakcji ze wskaźnikiem
   „Ostatnia aktualizacja: [znacznik czasu]".

---

### Historia użytkownika 3 — Zabezpieczenia antyszachrajskie i bezpieczeństwo kodów (Priorytet: P3)

System egzekwuje reguły zapobiegające nadużywaniu mechanizmu rabatowego: brak generowania
kodu przy zerowym saldzie, okres karencji między kolejnymi żądaniami kodów, ochrona przed
zatwierdzeniami na „widmowym saldzie" wynikającymi z wyścigu procesów oraz automatyczne
wygasanie kodów.

**Dlaczego ten priorytet**: Zabezpieczenia są wymagane w wersji produkcyjnej, ale mogą być
nakładane na działający przebieg P1; ścieżka szczęśliwa P1 może być weryfikowana niezależnie.

**Niezależny test**: Można przetestować przez próbę generowania kodu przy zerowym saldzie,
żądanie dwóch kodów w oknie karencji, wysłanie jednoczesnych żądań POS dla tego samego kodu
i weryfikację, że wszystkie są poprawnie odrzucane.

**Scenariusze akceptacyjne**:

1. **Mając** pracownika z saldem 0 PLN,
   **gdy** próbuje wygenerować kod,
   **to** API odmawia i zwraca błąd `ZEROWE_SALDO`.

2. **Mając** pracownika, który wygenerował kod 20 minut temu (karencja = 30 min),
   **gdy** próbuje wygenerować nowy kod,
   **to** API odmawia i zwraca błąd `AKTYWNA_KARENCJA` z pozostałym czasem oczekiwania.

3. **Mając** dwa jednoczesne żądania POS dla tego samego kodu w statusie `AKTYWNY`,
   **gdy** oba docierają do API w tej samej chwili,
   **to** dokładnie jedno zostaje zatwierdzone, a drugie odrzucone z błędem `JUŻ_WYKORZYSTANY`.

---

### Przypadki brzegowe

- Co się dzieje po 5 błędnych próbach podania PIN-u?
  Konto zostaje zablokowane na 15 minut; aplikacja wyświetla pozostały czas blokady.
  Po upływie 15 minut pracownik może próbować ponownie bez dodatkowej interwencji.

- Co się dzieje, gdy POS nigdy nie wysyła żądania finalizacji po zatwierdzeniu przez API?
  Kod pozostaje w stanie nierozstrzygniętym; zadanie czasowe MUSI go wygasić i zwolnić
  zarezerwowane saldo.
- Co się dzieje, gdy przypisanie koszyka pracownika zmienia się w trakcie miesiąca?
  Wartość rabatu zamrożona w transakcji MUSI odzwierciedlać koszyk w momencie tworzenia
  transakcji, nie bieżący koszyk.
- Co się dzieje, gdy API jest niedostępne w momencie generowania kodu?
  Aplikacja MUSI wyświetlić czytelny błąd; generowanie kodu offline jest niedozwolone.
- Co się dzieje, gdy API jest niedostępne podczas weryfikacji przez POS?
  POS MUSI otrzymać odpowiedź błędu; kasjer wraca do standardowej płatności pełną ceną.

## Wyjaśnienia

### Sesja 2026-04-10

- Q: Jak pracownik loguje się do aplikacji BonusApp? → A: Własny login BonusApp — numer pracownika + PIN (zarządzany lokalnie w bazie BonusApp)
- Q: Jaki poziom dostępności jest wymagany dla API BonusApp? → A: 99,5% miesięcznie (~3,6 h dopuszczalnego przestoju)
- Q: Czy endpoint logowania i generowania kodu wymagają rate limitingu poza karencją 30 min? → A: Tylko blokada konta po 5 błędnych próbach PIN (odblokowanie po 15 min); brak limitu IP
- Q: Jak długo historia transakcji i logi aktywności muszą być przechowywane? → A: 24 miesiące dla transakcji (wymóg regulacyjny), 6 miesięcy dla logów operacyjnych
- Q: Jak długo trwa sesja JWT pracownika w aplikacji mobilnej? → A: 8 godzin (jedna zmiana robocza)

## Wymagania *(wymagane)*

### Wymagania funkcjonalne

- **WF-001**: System MUSI umożliwiać pracownikowi z saldem > 0 PLN i brakiem aktywnej karencji
  wygenerowanie jednorazowego kodu rabatowego przez aplikację mobilną/www.
- **WF-002**: Wygenerowane kody MUSZĄ automatycznie wygasać po 15 minutach (status → WYGASŁY).
- **WF-003**: Każdy kod MUSI być możliwy do użycia dokładnie jeden raz; po finalizacji przez POS
  przechodzi w status WYKORZYSTANY, a każde kolejne użycie MUSI być odrzucone.
- **WF-004**: Integracja POS MUSI wysyłać zapytanie do API z identyfikatorem kodu i wartością
  brutto transakcji, otrzymując synchroniczną odpowiedź (zatwierdzenie lub odrzucenie).
- **WF-005**: API MUSI obliczać kwotę rabatu jako:
  `min(saldo, floor(wartość_transakcji × procent_rabatu_koszyka))` i weryfikować, że wynik
  nie przekracza ewentualnego miesięcznego limitu.
- **WF-006**: Po finalizacji przez POS API MUSI atomowo: oznaczyć kod jako WYKORZYSTANY,
  utworzyć rekord Transakcji (snapshot zamrożonego % rabatu, kwoty, znacznika czasu)
  i potrącić rabat z salda pracownika.
- **WF-007**: Aplikacja mobilna MUSI wyświetlać aktualne saldo pracownika, poziom rabatu koszyka,
  datę ważności środków oraz stronicowaną historię transakcji.
- **WF-008**: Aplikacja MUSI buforować lokalnie dane o saldzie i transakcjach w celu
  umożliwienia przeglądania offline.
- **WF-009**: System MUSI egzekwować karencję ≥ 30 minut między żądaniami generowania kodu
  dla tego samego pracownika.
- **WF-010**: System MUSI odmawiać generowania kodu gdy saldo pracownika = 0.
- **WF-011**: Dane o uprawnieniach pracownika i przypisaniu do koszyka MUSZĄ pochodzić
  z integracji z systemem kadrowo-płacowym; backend BonusApp NIE MOŻE duplikować danych
  z systemu HR.
- **WF-012**: API MUSI obsługiwać przebieg zwrotu/reklamacji, w którym zwrot zainicjowany
  przez POS uznaje kwotę rabatu na saldo pracownika i tworzy odpowiedni rekord Transakcji.
- **WF-013**: Środki bonusowe NIE MOGĄ być przenoszone między okresami rozliczeniowymi;
  wygasłe środki są zerowane na koniec okresu.
- **WF-014**: Jeśli zatwierdzenie transakcji spychałoby saldo pracownika poniżej 0, system
  MUSI odrzucić całą transakcję i zwrócić błąd `NIEWYSTARCZAJĄCE_SALDO`. Ujemne saldo jest
  niedozwolone. Kasjer informuje klienta o konieczności płatności pełną ceną.
- **WF-016**: Pracownik loguje się do aplikacji mobilnej za pomocą numeru pracownika (z systemu HR)
  i własnego PIN-u (4–6 cyfr) zarządzanego przez BonusApp. PIN jest przechowywany jako hash
  (bcrypt) w lokalnej bazie BonusApp. Po pomyślnym uwierzytelnieniu API wydaje token JWT
  z czasem ważności sesji. Pracownik MUSI móc samodzielnie zmienić PIN w aplikacji.
- **WF-019**: Token JWT wydawany po pomyślnym logowaniu MUSI wygasać po 8 godzinach.
  Po wygaśnięciu pracownik MUSI ponownie podać numer pracownika i PIN. Brak mechanizmu
  odświeżania tokenu — każda sesja wymaga pełnego uwierzytelnienia.
- **WF-018**: Rekordy transakcji MUSZĄ być przechowywane przez minimum 24 miesiące.
  Logi operacyjne (generowanie kodów, logowania, zdarzenia blokady konta) MUSZĄ być
  przechowywane przez minimum 6 miesięcy. Usunięcie danych przed upływem tych okresów
  jest niedozwolone.
- **WF-017**: Po 5 kolejnych błędnych próbach podania PIN-u konto pracownika MUSI zostać
  zablokowane na 15 minut. Pracownik MUSI otrzymać czytelny komunikat o blokadzie i czasie
  jej zakończenia. Licznik błędnych prób jest zerowany po pomyślnym logowaniu.
- **WF-015**: Uprawnienie do korzystania z systemu przysługuje wyłącznie pracownikom
  przypisanym do fizycznej placówki pracodawcy. Pracownicy centrali i biur regionalnych
  są wykluczeni z systemu BonusApp. Weryfikacja przypisania do placówki odbywa się na
  podstawie danych z systemu kadrowo-płacowego.

### Kluczowe encje

- **Użytkownik (Pracownik)**: Tożsamość systemowa powiązana z rekordem HR; przechowuje
  `aktualne_saldo`, `data_waznosci_srodkow`, `id_koszyka`, `ostatni_kod_wygenerowano_o`,
  `pin_hash` (bcrypt), `numer_pracownika` (unikalny, z systemu HR).
- **Koszyk**: Grupa rabatowa; przechowuje `procent_rabatu`, `miesięczny_limit_pln`
  oraz zbiór przypisanych ID użytkowników. Pochodzi z systemu kadrowo-płacowego.
- **Kod autoryzacyjny**: Jednorazowy OTP; przechowuje `wartość_kodu`, `id_użytkownika`,
  `status` (AKTYWNY / WYKORZYSTANY / WYGASŁY), `utworzono_o`, `wygasa_o`.
- **Transakcja**: Niezmienialny rekord zakupu; przechowuje `id_użytkownika`, `id_kodu`,
  `kwota_brutto`, `snapshot_procenta_rabatu`, `kwota_rabatu`, `kwota_netto`,
  `typ` (ZAKUP / ZWROT), `utworzono_o`.
- **UserSession / ActiveToken / TransactionHistoryLite**: Modele pamięci podręcznej po
  stronie klienta wyłącznie do wyświetlania offline; nigdy nieautorytatywne dla salda
  ani zatwierdzenia transakcji.

## Kryteria sukcesu *(wymagane)*

### Mierzalne wyniki

- **KS-001**: Pracownik może otworzyć aplikację, wygenerować kod i udostępnić go kasjerowi
  w ciągu 30 sekund w normalnych warunkach sieciowych.
- **KS-002**: POS otrzymuje odpowiedź API (zatwierdzenie lub odrzucenie) w ciągu 3 sekund
  od przesłania kodu i wartości transakcji.
- **KS-003**: Po finalizacji przez POS saldo pracownika jest zaktualizowane, a rekord
  transakcji widoczny w historii w ciągu 10 sekund.
- **KS-004**: Kod wygenerowany przez jednego pracownika nie może być pomyślnie użyty przez
  innego pracownika przy kasie — 0% przypadków współdzielenia kodów między pracownikami.
- **KS-005**: Wygasłe kody (starsze niż 15 min) są odrzucane w 100% przypadków.
- **KS-006**: Jednoczesne zduplikowane żądania POS dla tego samego kodu skutkują dokładnie
  jednym zatwierdzeniem — 0% zdarzeń podwójnego rabatu.
- **KS-007**: Aplikacja wyświetla zbuforowane saldo i historię bez dostępu do sieci przez
  co najmniej 24 godziny od ostatniej udanej synchronizacji.
- **KS-008**: API BonusApp osiąga dostępność ≥ 99,5% miesięcznie (dopuszczalny przestój
  ≤ 3,6 h/miesiąc). Przy niedostępności API kasjer stosuje standardową płatność pełną ceną
  bez konieczności eskalacji.
- **KS-009**: Rekordy transakcji są przechowywane przez co najmniej 24 miesiące od daty
  utworzenia. Logi operacyjne (generowanie kodów, próby logowania, zdarzenia blokady)
  są przechowywane przez co najmniej 6 miesięcy.

## Założenia

- System kadrowo-płacowy udostępnia API lub strumień zdarzeń z danymi profilu pracownika
  i przypisania do koszyka; BonusApp konsumuje te dane, ale nie jest ich właścicielem.
- System POS może być skonfigurowany do wywoływania zewnętrznego API HTTP; nie są wymagane
  zmiany w oprogramowaniu sprzętowym POS.
- Środki bonusowe są przydzielane miesięcznie przez system kadrowo-płacowy; BonusApp
  odbiera zdarzenie doładowania i rejestruje je na saldzie użytkownika.
- Środki NIE są przenoszone między okresami (wstępnie NIE).
- Aplikacja mobilna wymaga aktywnego połączenia z internetem do wygenerowania kodu;
  funkcjonalność offline ogranicza się do odczytu buforowanych danych.
- Ujemne saldo jest niedozwolone — transakcja skutkująca ujemnym saldem jest odrzucana w całości (WF-014).
- Uprawnieni są wyłącznie pracownicy przypisani do fizycznej placówki pracodawcy (WF-015).
- Przy zwrocie towaru rabat jest automatycznie uznawany na saldo pracownika, jednak wyłącznie
  jeśli żądanie zwrotu wpłynie do API w konfigurowalnym oknie czasowym od momentu transakcji
  (domyślnie: 48 godzin). Zwroty po upływie tego okresu wymagają ręcznej interwencji
  HR/finanse poza systemem BonusApp.
