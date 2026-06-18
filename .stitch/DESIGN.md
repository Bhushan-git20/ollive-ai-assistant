# Design System: Ollive AI Assistant

## 1. Visual Theme & Atmosphere
A restrained, gallery-airy interface with fluid spring-physics motion and confident asymmetric elements. The atmosphere is sleek, modern, and clinical yet warm — designed to feel like a high-end, premium native application rather than a generic web tool. 

## 2. Color Palette & Roles
## 2. Color Palette & Roles
## 2. Color Palette & Roles
- **Mesh Canvas** (Animated Gradient) — Fluid, shifting background using cool blues, indigos, teals, and soft pinks.
- **Glass Surfaces** (oklch(1 0 0 / 0.6)) — Cards and containers use semi-transparent white/dark with strong `backdrop-blur-xl`.
- **Deep Slate Gray** (oklch(0.2 0.02 200)) — Primary text, Deep depth
- **Deep Teal** (oklch(0.45 0.1 200)) — Premium primary accent for CTAs and focus rings
- **Bright Teal** (oklch(0.7 0.15 200)) — Dark mode active state accent
- **Glass Border** (oklch(1 0 0 / 0.4)) — Card borders, 1px structural lines

## 3. Typography Rules
- **Display:** Outfit — Track-tight, controlled scale, weight-driven hierarchy.
- **Body:** Outfit — Relaxed leading, 65ch max-width, neutral secondary color.
- **Mono:** Geist Mono — For code, metadata, timestamps, high-density numbers.
- **Banned:** Inter, generic system fonts for premium contexts. Serif fonts banned in dashboards.

## 4. Component Stylings
* **Buttons:** Flat, no outer glow. Tactile -1px translate on active. Accent fill for primary, ghost/outline for secondary.
* **Cards:** Generously rounded corners (0.75rem). Diffused whisper shadow. Used only when elevation serves hierarchy.
* **Inputs:** Label above, error below. Focus ring in accent color. No floating labels.
* **Loaders:** Skeletal shimmer matching exact layout dimensions. No circular spinners.
* **Empty States:** Composed, illustrated compositions.

## 5. Layout Principles
Grid-first responsive architecture. Strict single-column collapse below 768px. Max-width containment. No flexbox percentage math. Generous internal padding.

## 6. Motion & Interaction
Spring physics for all interactive elements. Staggered cascade reveals. Perpetual micro-loops on active dashboard components. Hardware-accelerated transforms only. 

## 7. Anti-Patterns (Banned)
- No emojis
- No Inter font
- No pure black (#000000)
- No neon glows or oversaturated accents
- No 3-column equal grids
- No AI copywriting clichés
- No broken image links
