# Fotos reales de producto

Coloca aquí fotos reales de productos/instalaciones Alamex (cabinas, componentes, elevadores instalados, etc.). El agente de Social Media las usa como foto real del post en vez de generarla con IA cuando una calza con el tema — más auténtico, y no gasta créditos de Higgsfield.

Cada foto que agregues necesita una entrada en `manifest.json` (lista de objetos):

```json
{
  "filename": "mrlg_cabina_frontal.jpg",
  "tags": ["MRL-G", "cabina", "interior", "acero inoxidable"],
  "description": "Cabina de acero inoxidable del MRL-G, vista frontal con puertas abiertas."
}
```

- `filename`: debe coincidir exactamente con el archivo en esta carpeta.
- `tags`: palabras clave que el agente usa para decidir si esta foto aplica a un post (modelo, tipo de escena, etc.).
- `description`: 1 frase describiendo lo que se ve — ayuda al agente a elegir bien y a redactar el `image_alt_text` si se reusa.

Si agregas fotos y me pides que las registre, las reviso y escribo el manifest yo mismo (igual que hice con `brand/reference_ads/`).

## Retoque automático (`raw/` → fondo de estudio)

Las fotos que usa el agente (las de esta carpeta, referenciadas en `manifest.json`) no son las fotos originales tal cual — pasan por un retoque determinístico (`integrations/media/product_retouch.py`, corrido vía `scripts/retouch_product_photos.py`): se recorta el producto de su fondo original (fábrica, pallets, piso) usando segmentación (`rembg`, no generativo — clasifica pixeles, nunca redibuja el producto) y se compone sobre un fondo de estudio limpio con sombra suave. El producto en sí queda pixel-por-pixel idéntico al original.

**Nunca uses un modelo generativo (Higgsfield u otro) para "mejorar" estas fotos** — se probó y altera la forma real del producto y reintroduce texto ilegible en las etiquetas (ver `guidelines.md`).

Los originales sin retocar viven en `raw/` (mismo nombre base). Para reprocesar (ej. si mejora el algoritmo de retoque, o agregas fotos nuevas a `raw/`):

```
python scripts/retouch_product_photos.py
```

Sobrescribe los `.png` en esta carpeta y actualiza `manifest.json` si cambió la extensión — no toca `raw/`.
