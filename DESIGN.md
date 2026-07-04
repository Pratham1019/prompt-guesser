<!-- SEED: re-run $impeccable document once there's code to capture the actual tokens and components. -->
---
name: Prompt Guesser
description: A neo-brutalist prompt-guessing game where players decode AI image prompts
colors:
  neutral-bg: "#F8F6F2"
  neutral-ink: "#111111"
  neutral-border: "#111111"
  accent-orange: "#FFA000"
  accent-blue: "#1C3BFF"
  accent-pink: "#FF1CAE"
  accent-yellow: "#E0FF1C"
  accent-green: "#1CFF3B"
typography:
  display:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "clamp(2.5rem, 8vw, 5rem)"
    fontWeight: 800
    lineHeight: 0.9
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Space Grotesk, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist Mono, IBM Plex Mono, monospace"
    fontSize: "0.875rem"
    fontWeight: 600
    letterSpacing: "0.05em"
rounded:
  none: "0px"
  sm: "2px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent-orange}"
    textColor: "{colors.neutral-ink}"
    rounded: "{rounded.none}"
    padding: "12px 24px"
  button-primary-hover:
    backgroundColor: "{colors.accent-pink}"
---

# Design System: Prompt Guesser

## 1. Overview

**Creative North Star: "The Neo-Brutalist Arcade"**

Prompt Guesser features an intentionally bold, raw, and tactile interface inspired by modern neo-brutalist web design and developer-centric visual languages. The system rejects corporate SaaS aesthetics, soft shadows, gradients, and glassmorphism. It frames the AI-generated gameplay within heavy black borders, asymmetric layouts, visible grids, and solid blocks of high-contrast saturated colors.

The design density is compact and high-contrast, structured like an arcade cabinet or a retro puzzle interface. The interactive elements feel mechanical—pressing a button translates it physically into the page, simulating a tactile micro-switch.

**Key Characteristics:**
- Thick solid black borders (`4px`) on all cards, inputs, and interactive components.
- Flat, high-contrast, non-blended background blocks with asymmetric offsets.
- Oversized geometric sans-serif headings paired with clean monospace secondary labels.
- Quick, snappy transitions with slight overshoots, mimicking physical switches.

## 2. Colors

The color palette anchors on an off-white base and utilizes pure black for ink and boundaries, layered with a secondary palette of high-contrast neon accents.

### Primary
- **Neo-Brutalist Base** (#F8F6F2 / oklch(0.97 0.005 80.0)): Used as the general application background, establishing a physical, paper-like surface.
- **Pure Black Ink & Border** (#111111 / oklch(0.12 0.0 0.0)): Used for all text, layout divisions, and solid borders.

### Accents
- **Arcade Orange** (#FFA000 / oklch(0.78 0.18 75.0)): The primary brand seed color, representing action, progress, and main interactive targets.
- **Electric Blue** (#1C3BFF / oklch(0.45 0.29 264.0)): Used for primary hints, active selection indicators, and success states.
- **Hot Pink** (#FF1CAE / oklch(0.60 0.28 340.0)): Used for primary guess buttons, score multipliers, and celebration highlights.
- **Acid Yellow** (#E0FF1C / oklch(0.94 0.24 108.0)): Used for warnings, countdown timers, and premium reveals.
- **Lime Green** (#1CFF3B / oklch(0.86 0.28 142.0)): Used for correct answers, greenlights, and score increases.

### Named Rules
**The Hard Border Rule.** All panels, cards, inputs, buttons, and display blocks must feature a solid, un-blurred black border (`#111111`) of at least `4px` (`2px` on smaller items).
**The Flat Block Rule.** Colors must be used as flat solid fills. Linear gradients, radial gradients, or transparent backdrop blurs (glassmorphism) are strictly prohibited.

## 3. Typography

The typographic system pairs an expressive, heavy geometric sans-serif for displays and titles with an uppercase monospace for settings, clues, and metadata.

**Display Font:** Space Grotesk (with system sans-serif fallback)
**Body Font:** Space Grotesk (with system sans-serif fallback)
**Label/Mono Font:** Geist Mono / IBM Plex Mono (with monospace fallback)

**Character:** Bold, punchy, structural, and readable. Headings look massive and mechanical, while prompt text segments look technical.

### Hierarchy
- **Display** (800, clamp(2.5rem, 8vw, 5rem), 0.9): Massive headers, game titles, and final screen score announcements.
- **Headline** (800, 2rem, 1.0): Section titles, round numbers, and large dialog headers.
- **Title** (700, 1.25rem, 1.2): Card headings, round counters, and active clue displays.
- **Body** (400, 1rem, 1.5): Clue descriptions, rules text, and helper info. Max line length: 65ch.
- **Label** (600, 0.875rem, 0.05em letters, uppercase): Interactive button labels, tags, timer counts, and setting titles.

### Named Rules
**The Tight Heading Rule.** Display and Headline headers must use a line-height of `0.9` to `1.0` and a letter-spacing of `-0.02em` to `-0.04em`. Wide line-heights are forbidden on large headings.

## 4. Elevation

The system rejects CSS box-shadow blurs. Depth is conveyed entirely through asymmetric layouts and flat offset shadows.

### Shadow Vocabulary
- **Tactile Card Shadow** (`box-shadow: 4px 4px 0px 0px #111111`): Used at rest on cards, panels, and buttons to give them height.
- **Tactile Card Shadow Pressed** (`box-shadow: 0px 0px 0px 0px #111111`): Used on active click or focus states.
- **Large Container Shadow** (`box-shadow: 8px 8px 0px 0px #111111`): Used for modals and main game board cards.

### Named Rules
**The Offset Depth Rule.** To elevate a card or button, offset it relative to its shadow. At rest, it has a `4px` black offset shadow. On hover, translate it by `-2px -2px` and increase the shadow to `6px 6px`. On click/active, translate it by `4px 4px` (down and right) and reduce the shadow to `0px 0px` to simulate a mechanical button press.

## 5. Components

### Buttons
- **Shape:** Square corners (0px radius) or very slight roundness (2px max).
- **Primary:** Filled with Arcade Orange (`#FFA000`), a solid black border (`4px`), and a black offset shadow. Text is uppercase monospace.
- **Hover / Focus:** Translate by `-2px -2px`, increase shadow to `6px 6px`, background swaps to Hot Pink (`#FF1CAE`).
- **Active / Pressed:** Translate by `4px 4px`, shadow becomes `0px 0px`.

### Cards / Containers
- **Corner Style:** Square (0px) or 2px radius.
- **Background:** White (`#FFFFFF`) or base neutral (`#F8F6F2`) for content, with solid accent blocks (e.g. Acid Yellow or Electric Blue header bars).
- **Border:** Solid `4px` black border.
- **Shadow Strategy:** Static `6px` or `8px` flat black offset shadow.

### Inputs / Fields
- **Style:** Flat white background, solid `4px` black border, monospace text.
- **Focus:** Translate by `-2px -2px`, generate a `4px` flat offset shadow in Electric Blue (`#1C3BFF`), keeping the black border.

### Navigation
- **Style:** Compact top bar with a solid `4px` bottom border, using monospace text for navigation items. Brand title is set in heavy display font.

## 6. Do's and Don'ts

### Do:
- **Do** use solid, high-contrast flat backgrounds for panels and sections.
- **Do** wrap every interactive element, text input, and card in a `4px` solid black border (`#111111`).
- **Do** simulate button clicks physically by translating the button coordinates (`transform: translate(4px, 4px)`) and setting the shadow offset to zero.
- **Do** use Space Grotesk in heavy weights (700 or 800) for display text.

### Don't:
- **Don't** use soft, blurry, transparent box-shadows.
- **Don't** use gradients, glassmorphism, or backdrop-filters.
- **Don't** default to standard corporate blue grids, light gray borders, or rounded corners greater than `2px`.
- **Don't** use lowercase letterforms or standard sans-serifs for metadata or status indicators (always uppercase monospace).
- **Don't** allow text to overlap or overflow container borders; reduce typography size clamp limits on smaller viewports.
