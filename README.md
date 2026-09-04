# Agentes de Marketing — MVP Semana 1

Gerente de Marketing (agente supervisor) + Social Media (agente subordinado) sobre LangGraph + API de Claude. La generación de imagen es agnóstica de backend (`integrations/media/`, contrato `MediaGenerator`): por defecto corre localmente (Stable Diffusion vía `diffusers`, sin créditos de API por imagen), y también hay adaptadores hospedados (Leonardo, fal.ai, Gemini, Higgsfield) seleccionables con `MEDIA_GENERATOR` en `.env` — video queda pospuesto por ahora. La publicación es agnóstica de plataforma (`integrations/social/`, contrato `SocialPublisher`): hoy hay adaptadores para Facebook y Mastodon, agregar una red nueva es escribir un adaptador más, sin tocar los agentes. Estado, métricas e imágenes generadas quedan en Supabase.

## Setup

1. `python -m venv .venv && .venv/Scripts/activate` (o el equivalente de tu shell)
2. Instala PyTorch con soporte CUDA **antes** que el resto (pip instala CPU-only por defecto en Windows aunque tengas GPU NVIDIA):
   ```
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
   ```
   (`cu130` funciona con el driver de esta máquina — CUDA 13.1 — porque los drivers NVIDIA son retrocompatibles. Si tu driver es más viejo, usa el índice `cuXXX` correspondiente de https://download.pytorch.org/whl/.)
   Luego: `pip install -r requirements.txt` (incluye `diffusers`/`transformers`, instalación pesada por el modelo de generación de imagen).
3. Copia `.env.example` a `.env` y completa las credenciales.
   - `ENABLED_PLATFORMS` controla a qué redes se publica (ej. `facebook`, `mastodon`, o `facebook,mastodon`) — solo hace falta llenar las credenciales de las que listes ahí.
   - `MEDIA_DEVICE=cuda` requiere una GPU NVIDIA con drivers CUDA instalados. Si no hay GPU, usa `MEDIA_DEVICE=cpu` (mucho más lento, minutos por imagen).
   - El modelo (`LOCAL_IMAGE_MODEL_ID`) se descarga automáticamente la primera vez que se genera una imagen (varios GB, puede tardar). Si Hugging Face pide aceptar una licencia para el modelo, crea una cuenta gratis, acéptala en la página del modelo, y genera un token de lectura para `HUGGINGFACE_TOKEN`.
4. Aplica el esquema en tu proyecto de Supabase: contenido de `scripts/setup_supabase_schema.sql`. También necesitas un bucket público de Storage llamado `post-media` (ver `integrations/supabase_client.py`) para que las imágenes generadas tengan una URL pública mostrable en el dashboard.
5. Completa `brand/guidelines.md` con la información real de la marca y coloca los logos (`brand/logo_primary.png`, etc.).

## Validar integraciones antes de correr el flujo completo

```
python scripts/smoke_test.py            # Supabase + lectura de cada plataforma habilitada
python scripts/smoke_test.py --publish  # además genera 1 imagen local y publica en cada plataforma habilitada
```

## Correr el flujo completo

```
python main.py "encárgate de la publicidad de esta semana"
```

El supervisor analiza desempeño reciente y decide cuántos posts hacer y de qué — pensado para uso semanal, no para pruebas rápidas.

## Publicar un post puntual, ahora mismo

```
python post_now.py "tema o brief del post, ej. la máquina gearless del MRL-L"
```

Salta la planeación semanal (no analiza engagement ni decide cuántos posts) y genera+publica un solo post directo — útil para pruebas o cuando ya sabes exactamente qué quieres publicar.

## Ver qué están haciendo los agentes

```
streamlit run dashboard.py
```

Corre localmente y lee directo de Supabase (la service role key nunca sale de tu máquina). Muestra el log de cada corrida (`agent_runs`), la decisión de estrategia semanal (`weekly_strategy`) y los posts generados/publicados por plataforma, con la imagen y el link a la publicación real (`posts`). Alternativa sin instalar nada: Supabase Studio → Table Editor sobre las mismas tres tablas.

## Tests

```
pip install pytest
pytest tests/ -v
```
