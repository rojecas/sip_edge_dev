---
name: svelte5
description: >
  Svelte 5 frontend skill for this project. Use when implementing or reviewing
  any Svelte 5 code (.svelte, .svelte.js, .js stores). Covers runes ($state,
  $derived, $effect), component API (mount vs new), store patterns, and
  common pitfalls with vite build vs dev.
---

# Svelte 5 — Reglas duras para sip_edge

## Runes: dónde y cómo

| Rune | Archivo | ¿OK? |
|------|---------|------|
| `$state`, `$derived` | `.svelte` | ✅ OK |
| `$state`, `$derived` | `.svelte.js` | ✅ OK (compilado por Svelte) |
| `$state`, `$derived` | `.js` | ❌ NO (no compilado → undefined) |
| `$effect` | `.svelte` (top-level) | ✅ OK |
| `$effect` | `.js` / `.svelte.js` (module-level) | ❌ NO (effect_orphan) |

## Component API

```js
// Svelte 4 (NO USAR)
import App from "./App.svelte";
const app = new App({ target: document.body });

// Svelte 5 (USAR)
import { mount } from "svelte";
import App from "./App.svelte";
const app = mount(App, { target: document.body });
```

## Stores compartidos (svelte/store)

```js
// ✅ Correcto: writable/derived en .js (NO requieren compilacion)
import { writable, derived, get } from "svelte/store";
export const token = writable(null);
export const isAdmin = derived([role], ([$r]) => $r === "admin");
```

En templates .svelte: usar prefix `$`
```svelte
<script>import { isAdmin } from "./stores/auth.js";</script>
{#if $isAdmin}...{/if}
```

`get(store)` es **snapshot** (no reactivo). Usar solo en callbacks/event handlers.

## Lifecycle (onMount, onDestroy)

- **Siempre** importar: `import { onMount } from "svelte";`
- `onMount` usa efecto interno → debe estar en `<script>` de `.svelte`, no en `.js`
- Preferir `onMount` sobre `$effect` para inicializacion (mas predecible)

## Reglas de templates

- `{#if}` dentro de snippet children (`<Layout><Child/></Layout>`) puede perder contexto → mover `{#if}` FUERA del wrapper
- `$storeName` (con `$`) es reactivo; sin `$` es snapshot
- Operadores ternarios en templates: `{$store && $store.prop ? val : "default"}`

## Build vs Dev

- `vite build` (prod): incluye runtime svelte completo
- `vite dev` (HMR): mejor para desarrollo rapido, recarga automatica
- Probar SIEMPRE en vite dev antes de build + deploy

## Checklist del implementer

- [ ] `main.js` usa `mount(App, {target})`, NO `new App()`
- [ ] Ningun `.js` usa `$state`/`$derived` (solo `.svelte.js`)
- [ ] Todo `onMount` tiene su `import { onMount }` explicito
- [ ] Stores usan `writable`/`derived` de `svelte/store`
- [ ] Templates usan `$storeName` para reactividad
- [ ] API responses: verificar `{items: [...]}` vs array directo
