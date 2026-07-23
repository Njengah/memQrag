# memQrag Demo UI

React + TypeScript + Tailwind CSS demo UI for memQrag, built with Vite.

## Status

This is a placeholder shell only. It has no product workflow logic yet — no chat
interface, no upload panel, no API calls. It exists to prove the frontend build
works end to end. See [`docs/PRODUCT_TIMELINE.md`](../docs/PRODUCT_TIMELINE.md)
(Phase 8) for the planned chat interface, memory panel, and side-by-side
standard RAG vs memQrag comparison.

## Local Development

```bash
npm install
npm run dev
```

## Build And Lint Checks

```bash
npm run build   # tsc -b && vite build
npm run lint    # oxlint
```

## Stack

- [Vite](https://vite.dev/)
- [React](https://react.dev/) + TypeScript
- [Tailwind CSS](https://tailwindcss.com/) via `@tailwindcss/vite`
