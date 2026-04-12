# Design System Document: The Editorial Professional

## 1. Overview & Creative North Star
**Creative North Star: The Sovereign Ledger**
This design system moves away from the sterile, "template-heavy" nature of corporate fintech and toward a high-end editorial experience. We are not building a simple utility; we are building a platform of recognition. The aesthetic is "Sovereign"—authoritative, calm, and premium. 

To achieve this, we break the rigid mobile grid. We utilize **intentional asymmetry**, where text heavy blocks are balanced by expansive white space. We favor **overlapping elements** to create a sense of physical assembly, and we leverage a dramatic typography scale to ensure the "Bonus" feels like an event, not just a line item. This system is designed specifically for the retail environment: high-legibility for fast-paced shifts, and large touch targets for effortless one-handed interaction.

---

## 2. Colors & Tonal Depth
Our palette is anchored by a deep, authoritative Dark Green (`primary: #00502e`), conveying stability and growth. 

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Traditional "boxes" make an app feel dated and cramped. Boundaries must be defined solely through background color shifts or tonal transitions.
*   *Implementation:* A card (`surface-container-lowest`) sits on a background (`surface-container-low`) to create separation.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, premium paper stocks.
*   **Base:** `surface` (#f8f9fa)
*   **De-emphasized zones:** `surface-container-low` (#f3f4f5)
*   **Interactive Cards:** `surface-container-lowest` (#ffffff)
*   **Elevated Overlays:** `surface-bright` (#f8f9fa)

### The "Glass & Gradient" Rule
To elevate the experience beyond "standard" Material Design:
*   **Glassmorphism:** For floating headers or navigation bars, use `surface` at 80% opacity with a `20px` backdrop-blur. This keeps the user grounded in their scroll position.
*   **Signature Textures:** Main CTAs should never be flat. Apply a subtle linear gradient from `primary` (#00502e) to `primary_container` (#006b3f) at a 135-degree angle to add "soul" and a tactile, metallic quality.

---

## 3. Typography
We use a dual-typeface system to balance editorial character with functional clarity.

*   **Display & Headlines (Public Sans):** Used for "The Moment." When an employee receives a bonus, we use `display-lg` to make the numbers feel monumental. Public Sans provides a sturdy, corporate-yet-modern foundation.
*   **Body & Labels (Inter):** Inter is our workhorse. Its tall x-height ensures that even at `body-sm` (0.75rem), retail employees can read terms and conditions in low-light backrooms or bright storefronts.

**Hierarchy as Identity:** 
High contrast is mandatory. Pair a `headline-lg` title with a `body-md` description. The gap in scale creates an editorial "look" that guides the eye immediately to the most important data point.

---

## 4. Elevation & Depth
Depth is not achieved through shadows alone, but through **Tonal Layering.**

### The Layering Principle
Stacking tiers creates natural depth. 
*   *Example:* Place a `surface-container-lowest` card (Pure White) onto a `surface-container` (#edeeef) background. The contrast provides all the "lift" required.

### Ambient Shadows
Shadows must be "atmospheric." 
*   **Formula:** Blur: 24px–40px | Opacity: 4%–6% | Color: Derived from `on-surface` (#191c1d). 
*   Avoid dark grey drop shadows; they muddy the "Light/Trusted" aesthetic.

### The "Ghost Border" Fallback
If a layout requires a border for accessibility (e.g., in high-glare environments), use a **Ghost Border**:
*   `outline-variant` (#bec9bf) at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons (The "One-Handed" Standard)
*   **Primary:** Gradient (`primary` to `primary_container`), `xl` (0.75rem) roundedness. Minimum height: 56px to accommodate one-handed thumb taps.
*   **Secondary:** No fill. `Ghost Border` with `on_secondary_fixed_variant` text.
*   **States:** On press, increase depth by shifting from a gradient to a solid `primary_container` fill.

### Cards & Lists (The "Breathable" Rule)
*   **Forbidden:** Divider lines. 
*   **Allowed:** Use 16px–24px of vertical white space (from our spacing scale) to separate list items. 
*   **Grouping:** Use `surface-container-low` as a "well" to group related list items together.

### Input Fields
*   **Aesthetic:** "Understated Elegance." Use a `surface-container-highest` fill with no border. Upon focus, transition to a `primary` (2px) bottom-accent line only.
*   **Touch Targets:** All inputs must maintain a 56px height.

### Recognition Chips
*   Used for "Bonus Types" (e.g., Performance, Anniversary). Use `secondary_container` with `on_secondary_container` text. Use `full` (9999px) roundedness to contrast against the `xl` (0.75rem) corners of cards.

---

## 6. Do's and Don'ts

### Do
*   **Do** use asymmetrical margins. A wider left-hand margin for headlines creates a sophisticated, editorial "gut" in the layout.
*   **Do** prioritize WCAG AA contrast. Ensure `on_primary` text is always used over `primary` backgrounds.
*   **Do** use `surface-tint` for subtle brand moments, like the background of a success state icon.

### Don't
*   **Don't** use 100% black. Use `on_surface` (#191c1d) for all text to maintain a premium, "ink-on-paper" feel.
*   **Don't** use standard "Material Blue" for links. Use `primary` (#00502e) or `tertiary` (#782b31) for a bespoke corporate feel.
*   **Don't** crowd the screen. If a retail employee can't parse the screen in 2 seconds, there is too much information. Increase the "Surface Hierarchy" nesting to hide secondary details.