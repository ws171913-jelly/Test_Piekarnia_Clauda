# Design System — BonusApp (Artisan Hearth)

Dokument opisuje obowiązujące zasady wizualne. Wszystkie nowe ekrany i komponenty **muszą** być z nimi zgodne.
Źródło prawdy dla kolorów, odstępów i promieni zaokrągleń jest `mobile/src/theme.ts`.

---

## 1. Motyw i nastrój

Aplikacja dla pracowników rzemieślniczej piekarni. Klimat: ciepły, organiczny, premium — jak ręcznie zrobiony chleb w papierowej torebce. Odwołania wizualne do papieru, faktury chleba, naturalnych barw pszenicy i kawy.

**Nie robimy** sterylnej aplikacji korporacyjnej. **Robimy** narzędzie, które pracownik chce wyjąć z kieszeni.

---

## 2. Kolory

Paleta pochodzi z systemu Material You — `Artisan Hearth`. Kody są ostateczne; nie wolno używać innych wartości hex.

```ts
// mobile/src/theme.ts → colors
primary:                '#6c593a'   // ciepły brąz — główna marka
onPrimary:              '#ffffff'
primaryContainer:       '#867151'
primaryFixed:           '#f9dfb7'
primaryFixedDim:        '#dcc39d'
onPrimaryFixed:         '#261902'
inversePrimary:         '#dcc39d'

secondary:              '#425e90'   // niebieski akcent
onSecondary:            '#ffffff'
secondaryContainer:     '#abc7ff'
onSecondaryContainer:   '#365283'

error:                  '#ba1a1a'
onError:                '#ffffff'
errorContainer:         '#ffdad6'
onErrorContainer:       '#93000a'

surface:                '#fff8f3'   // tło aplikacji — ciepła biel
onSurface:              '#221a0e'   // tekst główny — nie czysty czarny
onSurfaceVariant:       '#4d463c'   // tekst pomocniczy

surfaceContainerLowest: '#ffffff'
surfaceContainerLow:    '#fff2e3'   // karty, formularze
surfaceContainer:       '#fcebd8'
surfaceContainerHigh:   '#f6e6d2'
surfaceContainerHighest:'#f0e0cd'   // pola input, awatary
surfaceDim:             '#e8d8c4'

outline:                '#7e766b'
outlineVariant:         '#d0c5b8'   // delikatne obramowania / separatory
```

### Zasady użycia kolorów

- Tło ekranów: zawsze `colors.surface` (`#fff8f3`).
- Karty i sekcje formularza: `colors.surfaceContainerLow`.
- Pola tekstowe (input): `colors.surfaceContainerHighest`.
- Akcenty niebieskie (`secondary`, `secondaryContainer`) — tylko dla rabatów i oznaczeń "Zakup".
- Nigdy nie używaj czystego czarnego (`#000000`). Tekst główny to `colors.onSurface`.
- Obramowania jawne są **zabronione**. Separację tworzysz przez zmianę koloru tła (surface hierarchy).
  Jedynym wyjątkiem jest `borderLeftWidth: 4` dla banerów błędów (lewa krawędź w kolorze `colors.error`).

---

## 3. Typografia

### Fonty (Google Fonts — załadowane w `mobile/public/index.html`)

```ts
// mobile/src/theme.ts → fonts
fonts.headline = 'Newsreader'          // szeryfowy, nagłówki i tytuły
fonts.body     = "'Plus Jakarta Sans'" // bezszeryfowy, teksty i etykiety
```

Google Fonts URL (jeden request dla wszystkich fontów):
```
https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0..1,0&display=swap
```

### Zastosowanie

| Zastosowanie | Font | Styl | Rozmiar |
|---|---|---|---|
| Główny tytuł ekranu (np. "Witaj, Jan") | `fonts.headline` | italic, weight 600–700 | 28–42 |
| Nagłówki sekcji (np. "Ostatnie transakcje") | `fonts.headline` | weight 600–700 | 20–26 |
| Nazwa marki "BonusApp" | `fonts.headline` | italic, weight 700 | 20–42 |
| Kwota pieniężna (saldo, transakcja) | `fonts.headline` | weight 700 | 16–34 |
| Tytuł karty, podpis karty | `fonts.headline` | weight 600–700 | 17–24 |
| Etykiety UPPERCASE (np. "DOSTĘPNE SALDO") | brak (system) | weight 700, letterSpacing ≥ 2 | 9–11 |
| Tekst pomocniczy, opisy | brak (system) | weight 400–500 | 11–14 |
| Przyciski | brak (system) | weight 700, letterSpacing 1 | 13–15 |
| Kod OTP (jednorazowy) | `'monospace'` (`'Courier New'`) | weight 700, letterSpacing 8 | 44 |

**Zasady:**
- `fontFamily: 'serif'` — nigdy nie używaj. Zawsze importuj `fonts` z `../theme` i użyj `fonts.headline`.
- Nagłówki tytułowe (nazwa ekranu w headerze) zawsze `fontStyle: 'italic'`.
- Etykiety kategorii (np. "NUMER PRACOWNIKA", "DOSTĘPNE SALDO") — uppercase + letterSpacing, bez specjalnego fontu.

---

## 4. Odstępy (`spacing`)

```ts
spacing.xs  = 4
spacing.sm  = 8
spacing.md  = 16
spacing.lg  = 24
spacing.xl  = 32
spacing.xxl = 48
```

- Padding główny ekranów: `paddingHorizontal: spacing.lg` (24).
- Padding kart/sekcji: `padding: spacing.xl` (32) lub `spacing.lg` (24).
- Odstępy między elementami w kartach: `gap: spacing.md` lub `spacing.lg`.
- `paddingBottom` listy scroll: ≥ 100, żeby ostatni element nie chował się za dolny pasek.

---

## 5. Zaokrąglenia (`radius`)

```ts
radius.sm   = 4
radius.md   = 8
radius.lg   = 12
radius.xl   = 16
radius.full = 9999
```

- Karty, kontenery sekcji: `radius.xl` (16).
- Przyciski CTA, inputy: `radius.lg` (12) lub `radius.xl` (16).
- Chipy (filtry, odznaki): `radius.full` (9999).
- Awatary i kółka ikon: `borderRadius = połowa szerokości` (np. `width: 44, borderRadius: 22`).
- Dolny pasek nawigacji: `borderTopLeftRadius: 32, borderTopRightRadius: 32`.

---

## 6. Cienie

Cienie są "atmosferyczne" — rozmyte, bardzo lekkie. Wzorzec:

```ts
shadowColor: '#221a0e',
shadowOffset: { width: 0, height: 8–12 },
shadowOpacity: 0.04–0.08,
shadowRadius: 16–40,
elevation: 2–8,
```

- Ciemny cień (`#000`) — zabroniony.
- Duże karty (saldo, kod): `shadowRadius: 40, shadowOpacity: 0.06–0.08`.
- Małe karty i chipy: `shadowRadius: 16, shadowOpacity: 0.04–0.05`.

---

## 7. Struktura ekranu

### Header (górna belka)

Każdy ekran podrzędny (nie dashboard) ma header:
```tsx
<View style={styles.header}>
  <Pressable onPress={onBack} style={styles.backBtn}>
    <Text style={styles.backIcon}>←</Text>  {/* fontSize: 22, color: colors.primary */}
  </Pressable>
  <Text style={styles.headerTitle}>Tytuł ekranu</Text>  {/* fonts.headline, italic */}
  <View style={styles.backBtn} />  {/* placeholder dla symetrii LUB avatar/ikona */}
</View>
```

Styl headera:
```ts
paddingHorizontal: spacing.lg,
paddingTop: spacing.xl + spacing.md,  // dużo miejsca od góry
paddingBottom: spacing.md,
backgroundColor: colors.surface,
```

### Dolny pasek nawigacji (`App.tsx`)

- 3 zakładki: Dashboard (`dashboard`), Historia (`history`), Profil (`person`).
- Ikony: **Material Symbols Outlined** przez komponent `MatIcon` (span na web, emoji na native).
- Aktywna zakładka: `backgroundColor: colors.primary`, ikona wypełniona (`FILL 1`), kolor `colors.onPrimary`.
- Nieaktywna: kolor ikon `colors.onSurfaceVariant`.
- Etykiety: uppercase, `letterSpacing: 1`, `fontSize: 9`.

### Hero image (nagłówek z obrazkiem)

Wzorzec stosowany w ekranach logowania, zmiany PINu:
```tsx
<View style={{ height: 180–200, borderRadius: radius.xl, overflow: 'hidden' }}>
  <Image source={...} style={{ flex: 1, width: '100%' }} resizeMode="cover" />
  <View style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 60–80,
                 backgroundColor: colors.surface, opacity: 0.6 }} />
</View>
```
Nad zdjęciem — karta `surfaceContainerLow` z ujemnym `marginTop` (nakładka).

---

## 8. Karty i komponenty

### Karta salda (BalanceScreen)

- Obraz tła (`balance-card-bread.png`), height: 200, `borderRadius: radius.xl`.
- Nakładka gradientu: `backgroundColor: colors.primary, opacity: 0.7`, od dołu ~100px.
- Overlay card: `marginTop: -80`, `borderRadius: radius.xl`, `surfaceContainerHighest`.

### Karta transakcji

```tsx
<View style={{ flexDirection: 'row', backgroundColor: colors.surfaceContainerLow,
               borderRadius: radius.xl, padding: spacing.md, gap: spacing.md }}>
  <View style={{ width: 44, height: 44, borderRadius: 22,
                 backgroundColor: colors.surfaceContainerHighest }}>
    <Text>{isRefund ? '↩️' : '🛒'}</Text>
  </View>
  {/* typ + data + kwota */}
</View>
```
- Zakup: kwota czerwona (`colors.error`), prefiks `-`.
- Zwrot: kwota zielona/primary (`colors.primary`), prefiks `+`.

### Promo card

```tsx
<View style={{ flexDirection: 'row', backgroundColor: colors.surfaceContainerLow,
               borderRadius: radius.xl, padding: spacing.md }}>
  <View style={{ width: 80, height: 80, borderRadius: 40, borderWidth: 4,
                 borderColor: colors.surfaceContainerHighest, overflow: 'hidden' }}>
    <Image ... />
  </View>
  <View>{/* tytuł (fonts.headline) + opis */}</View>
</View>
```

### Banery błędów i blokad

Error (nie-krytyczny):
```ts
flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
backgroundColor: colors.errorContainer + '66',  // 40% opacity
borderRadius: radius.md,
borderLeftWidth: 4, borderLeftColor: colors.error,
```

Blokada konta:
```ts
flexDirection: 'row', backgroundColor: colors.surfaceContainerLow,
borderRadius: radius.xl, borderWidth: 1, borderColor: colors.error + '1a',
```
Z ikoną w kółku `backgroundColor: colors.error + '1a'`.

### Przyciski CTA

Główny:
```ts
backgroundColor: colors.primary, borderRadius: radius.lg,
paddingVertical: spacing.md + 2,  // ~18px
color: colors.onPrimary, fontWeight: '700', letterSpacing: 1, textTransform: 'uppercase',
```
Wyłączony: `opacity: 0.4–0.5`.

Drugorzędny (powrót):
```ts
backgroundColor: colors.surfaceContainer, borderRadius: radius.lg,
color: colors.primary, fontWeight: '700',
```

### Pola tekstowe

```ts
backgroundColor: colors.surfaceContainerHighest,
borderRadius: radius.xl, padding: spacing.md,
flexDirection: 'row', alignItems: 'center',
// input: fontSize: 16–20, color: colors.onSurface
```

Wariant "minimalistyczny" (LoginScreen): brak ramki, tylko `inputUnderline` — `height: 2, backgroundColor: colors.outlineVariant, opacity: 0.3`.

---

## 9. Ikony

### Material Symbols Outlined

Używane w dolnym pasku i interfejsie webowym. Komponent `MatIcon` w `App.tsx`:
```tsx
// Web:
<span className="material-symbols-outlined"
  style={{ fontVariationSettings: filled ? "'FILL' 1, 'wght' 400" : "'FILL' 0, 'wght' 400" }}>
  {name}
</span>

// Native: emoji fallback
```

Klasa CSS `.material-symbols-outlined` musi być zadeklarowana w `public/index.html`.

### Emoji jako ikony stanu

Dopuszczalne dla stanu (błąd, oczekiwanie, sukces) i ikonek listy transakcji:
`⚠️` błąd, `⏳` karencja, `↩️` zwrot, `🛒` zakup, `🔒` blokada, `⎋` wyloguj.

---

## 10. Obrazy (`mobile/src/assets/img/`)

Wszystkie obrazy w jednym katalogu — nie tworzyć podkatalogów.

| Plik | Użycie |
|---|---|
| `balance-card-bread.png` | karta salda (BalanceScreen) |
| `bread-basket.png` | pusty stan historii (HistoryScreen) |
| `change-pin-header.png` | hero ChangePinScreen |
| `code-card-texture.png` | banner aktywnego kodu (CodeDisplayScreen) |
| `code-no-balance-bowl.png` | stan braku salda (CodeDisplayScreen) |
| `coffee-circle.png` | promo card (BalanceScreen) |
| `hero-bakery.png` | hero LoginScreen |
| `history-avatar.png` | avatar w headerze historii |

Nowe obrazy: umieszczać w `mobile/src/assets/img/`, importować przez `require('../assets/img/nazwa.png')`.

---

## 11. Web (react-native-web)

Aplikacja działa w przeglądarce przez webpack + react-native-web. Wymagania:

`public/index.html` musi zawierać:
```html
<!-- Google Fonts — jeden request -->
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@...&family=Plus+Jakarta+Sans:...&family=Material+Symbols+Outlined:...&display=swap" rel="stylesheet" />

<style>
  *, *::before, *::after { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; padding: 0; background: #fff8f3; -webkit-tap-highlight-color: transparent; }
  #root { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
  .material-symbols-outlined { font-family: 'Material Symbols Outlined'; ... }
</style>
```

Aplikacja musi zajmować 100% okna przeglądarki. Jeśli `flex: 1` nie działa — sprawdź `height: 100%` na `html`, `body`, `#root`.

---

## 12. Checklist dla nowego ekranu

Przed oddaniem ekranu sprawdź:

- [ ] Import: `import { colors, fonts, radius, spacing } from '../theme'`
- [ ] Tło: `backgroundColor: colors.surface`
- [ ] Fonty nagłówków: `fontFamily: fonts.headline` (nigdy `'serif'`)
- [ ] Fonty body: brak jawnego `fontFamily` (system) lub `fontFamily: fonts.body`
- [ ] Cień: `shadowColor: '#221a0e'`, opacity ≤ 0.08
- [ ] Brak czystego czarnego w kolorach tekstu lub tła
- [ ] Brak jawnych obramowań (poza wyjątkami: baner błędu, awatar z obwódką)
- [ ] Header podrzędny: strzałka `←`, tytuł italic `fonts.headline`, placeholder lub ikona po prawej
- [ ] Dolny padding listy: ≥ 100 (`paddingBottom: 100`)
- [ ] Obrazy: w `mobile/src/assets/img/`, `resizeMode="cover"`
