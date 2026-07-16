# Flowy Design System (FDS)

Flowy's visual language is built for **clarity under complexity** — a dark-first interface where workflow structure, execution state, and node semantics are immediately readable.

## Principles

1. **Flow over decoration** — Visual hierarchy follows execution path. Accent color draws the eye along the graph, not into chrome.
2. **Semantic color** — Every node type has a dedicated hue. Users learn the palette once and read workflows at a glance.
3. **Quiet surfaces** — Panels and chrome recede. The canvas is the hero; UI furniture uses low-contrast slate tones.
4. **Precision typography** — Geometric sans for UI, monospace for IDs, configs, and code.
5. **Tactile depth** — Subtle elevation and soft glow on interactive elements; never flat, never noisy.

---

## Color Palette

### Surfaces (dark theme)

| Token | Value | Usage |
|-------|-------|-------|
| `--fds-bg-base` | `#080B10` | App background |
| `--fds-bg-raised` | `#0F1419` | Sidebar, toolbar |
| `--fds-bg-panel` | `#151B23` | Cards, property panels |
| `--fds-bg-canvas` | `#0C1017` | Workflow canvas |
| `--fds-border-subtle` | `#1E2733` | Dividers, node borders |
| `--fds-border-strong` | `#2D3A4D` | Focus rings, selected states |

### Text

| Token | Value | Usage |
|-------|-------|-------|
| `--fds-text-primary` | `#F1F5F9` | Headings, node labels |
| `--fds-text-secondary` | `#94A3B8` | Descriptions, metadata |
| `--fds-text-muted` | `#64748B` | Placeholders, hints |
| `--fds-text-inverse` | `#080B10` | Text on bright accents |

### Brand & Actions

| Token | Value | Usage |
|-------|-------|-------|
| `--fds-brand` | `#22D3EE` | Primary actions, active nav, connection lines |
| `--fds-brand-dim` | `#0891B2` | Hover states |
| `--fds-brand-glow` | `rgba(34, 211, 238, 0.25)` | Focus glow |

### Node Type Accents

| Type | Token | Color | Meaning |
|------|-------|-------|---------|
| Trigger | `--fds-node-trigger` | `#F43F5E` | Entry points |
| LLM | `--fds-node-llm` | `#A78BFA` | AI reasoning |
| Tool | `--fds-node-tool` | `#38BDF8` | Python functions |
| MCP | `--fds-node-mcp` | `#2DD4BF` | External MCP tools |
| Approval | `--fds-node-approval` | `#FBBF24` | Human-in-the-loop |
| Notification | `--fds-node-notification` | `#34D399` | Outbound alerts |

Each node accent has a companion `--fds-node-*-bg` at 12% opacity for fills.

### Status

| Token | Color | Usage |
|-------|-------|-------|
| `--fds-status-running` | `#22D3EE` | Active execution |
| `--fds-status-waiting` | `#FBBF24` | Awaiting approval |
| `--fds-status-completed` | `#34D399` | Success |
| `--fds-status-failed` | `#F87171` | Error |

---

## Typography

| Role | Family | Weight | Size |
|------|--------|--------|------|
| Display | Plus Jakarta Sans | 700 | 24–32px |
| Heading | Plus Jakarta Sans | 600 | 16–20px |
| Body | Plus Jakarta Sans | 400–500 | 13–14px |
| Caption | Plus Jakarta Sans | 500 | 11–12px |
| Mono | IBM Plex Mono | 400 | 12–13px |

**Scale:** 11 / 12 / 13 / 14 / 16 / 20 / 24 / 32 px

---

## Spacing

Base unit: **4px**

| Token | Value |
|-------|-------|
| `--fds-space-1` | 4px |
| `--fds-space-2` | 8px |
| `--fds-space-3` | 12px |
| `--fds-space-4` | 16px |
| `--fds-space-5` | 20px |
| `--fds-space-6` | 24px |
| `--fds-space-8` | 32px |

---

## Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--fds-radius-sm` | 6px | Badges, chips |
| `--fds-radius-md` | 10px | Buttons, inputs |
| `--fds-radius-lg` | 14px | Panels, nodes |
| `--fds-radius-xl` | 20px | Modals |

---

## Elevation

| Token | Shadow |
|-------|--------|
| `--fds-shadow-sm` | `0 1px 2px rgba(0,0,0,0.4)` |
| `--fds-shadow-md` | `0 4px 12px rgba(0,0,0,0.35)` |
| `--fds-shadow-lg` | `0 8px 32px rgba(0,0,0,0.45)` |
| `--fds-shadow-glow` | `0 0 24px var(--fds-brand-glow)` |

---

## Motion

| Token | Value | Usage |
|-------|-------|-------|
| `--fds-duration-fast` | 120ms | Hover, toggle |
| `--fds-duration-normal` | 200ms | Panel slide, node select |
| `--fds-duration-slow` | 320ms | Page transitions |
| `--fds-ease` | `cubic-bezier(0.4, 0, 0.2, 1)` | Default easing |

---

## Components

### Buttons
- **Primary** — Brand fill, dark text, glow on hover
- **Secondary** — Panel bg, subtle border
- **Ghost** — Transparent, text only
- **Danger** — Failed status color

### Nodes (workflow canvas)
- 220px min-width card with left accent stripe (4px) in node-type color
- Icon in tinted circle (node-type bg)
- Label + optional subtitle
- Connection handles: 10px circles, brand color when connected

### Panels
- `--fds-bg-panel` background
- 1px `--fds-border-subtle` border
- `--fds-radius-lg` corners
- `--fds-shadow-md` elevation

---

## Usage

Import tokens in TypeScript:

```ts
import { tokens, nodeColors } from '@/design-system/tokens';
```

Global styles are applied via `src/design-system/index.css`, imported in `main.tsx`.

All UI components in `src/components/ui/` consume FDS tokens exclusively — no ad-hoc hex values in feature code.
