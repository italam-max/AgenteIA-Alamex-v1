# Panel de Agentes de Marketing — Alamex

Panel web (Next.js + shadcn/ui) para ver qué hacen los agentes de marketing de Alamex, qué
publican, y ajustar su configuración superficial sin tocar código. Reemplaza a `dashboard.py`
(Streamlit) como la vista recomendada.

Corre **solo local** — sin login, sin deploy. Lee/escribe directo los mismos archivos que usa el
proyecto Python (`../brand/guidelines.md`, `../brand/equipment_catalog.md`,
`../brand/product_photos/`, `../.env`) porque ambos corren en la misma máquina; los cambios
aplican en la próxima corrida de `main.py`/`post_now.py` sin reiniciar nada.

## Setup

1. `npm install`
2. Copia los valores de Supabase de `../.env` a `.env.local` (ya debería existir con los valores
   correctos si vino del repo clonado con `.env.local` — si no, créalo):
   ```
   SUPABASE_URL=...
   SUPABASE_SERVICE_ROLE_KEY=...
   PYTHON_VENV_PATH=..\.venv\Scripts\python.exe
   ```
3. `npm run dev` → `http://localhost:3000`

## Páginas

- **Agentes** (`/`) — qué hace cada agente y su actividad reciente.
- **Corridas** (`/corridas`) — historial + bitácora en vivo.
- **Posts** (`/posts`) — galería de todo lo publicado.
- **Estrategia** (`/estrategia`) — historial de decisiones semanales.
- **Configuración** (`/configuracion`) — tono de marca, plataformas/generador de imagen, modelo
  destacado de la semana, fotos reales de producto (incluye subir una foto nueva + retocarla).
- **Crecimiento** (`/crecimiento`) — inicia/detiene `run_growth_mission.py` (ver README principal)
  y muestra su bitácora en vivo. El proceso corre atado a este servidor de desarrollo, no
  independiente (`src/lib/growthProcess.ts`) — **reiniciar `npm run dev` mata la misión en curso**;
  vuelve a iniciarla desde la pestaña después de reiniciar.

## Seguridad

La Supabase service role key vive solo en `.env.local` y solo se usa dentro de Route Handlers
(`src/app/api/**`) y Server Components — nunca en un archivo `"use client"`, nunca llega al
navegador. Las API keys de `.env` (Anthropic, Higgsfield, etc.) nunca se leen ni se exponen desde
el panel — solo `ENABLED_PLATFORMS`/`MEDIA_GENERATOR` son editables (`src/lib/envFile.ts`, allow-list
explícita).

## Notas técnicas

- `src/lib/repoPaths.ts` resuelve las rutas al repo Python (asume que `dashboard-web/` es un
  sibling folder dentro del mismo repo).
- Subir una foto de producto invoca `python scripts/retouch_product_photos.py <archivo>` con el
  venv de Python (`child_process.execFile`) — tarda ~30-90s, la retocada resultante (rembg, no
  generativa) se guarda en `brand/product_photos/` y su entrada se agrega a `manifest.json`.
