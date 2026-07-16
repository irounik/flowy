# Flowy Frontend

Visual workflow designer for the Flowy async agentic workflow platform.

## Stack

- **React 19** + **Vite** + **TypeScript**
- **Tailwind CSS v4** with the Flowy Design System (FDS)
- **@xyflow/react** for drag-and-drop workflow canvas

## Design System

See [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) for the full FDS specification — colors, typography, spacing, node semantics, and component guidelines.

All UI components consume FDS tokens from `src/design-system/`.

## Development

```bash
npm install
npm run dev
```

Runs at `http://localhost:5173` with API proxy to `http://localhost:8000`.

## Features

- **Drag-and-drop canvas** — Drag node types from the palette or click to add
- **Six node types** — Trigger, LLM, Tool, MCP, Approval, Notification
- **Properties panel** — Configure selected node settings
- **Templates** — Pre-built Invoice Approval and Research workflows
- **Save / Export** — Local storage + JSON export
- **Run** — Trigger execution via backend API

## Build

```bash
npm run build
npm run preview
```
