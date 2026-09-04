# Guías de marca

Este archivo se inyecta en el prompt (cacheado) de ambos agentes. Las secciones marcadas "(pendiente)" siguen siendo plantilla — complétalas cuando tengas la info para mejorar más la calidad del contenido.

## Rubro
Alamex fabrica y vende elevadores (ver `equipment_catalog.md` para el catálogo completo con especificaciones reales).

## Tono de voz
**(borrador — primera pasada, corregir/ajustar según feedback real)**. Basado en el copy de las 16 piezas reales (`brand/reference_ads/`): directo y técnico pero accesible, sin jerga corporativa vacía. Rasgos concretos:
- Habla en primera persona plural ("en Alamex...", nunca "nosotros los expertos..." — sin autobombo).
- Confiado por los datos, no por adjetivos: la cifra real (kg, personas, paradas, m/s) es el argumento, no "el mejor" o "líder en el mercado".
- Modo educativo/curioso cuando aplica ("¿Sabías que...?", dato o cifra sorprendente primero, explicación después) — es el gancho que más usa el equipo real.
- Cierra invitando a la conversación (pregunta concreta o CTA específico), no con un genérico "conoce más" — clave para generar respuestas en una red chica como Mastodon.
- Nunca alarmista ni de venta agresiva; el tono es de asesor técnico que informa, no de vendedor que presiona.

## Mensajes clave / propuesta de valor
**(borrador — primera pasada)**:
- Especificidad técnica real por encima de superlativos: capacidad exacta, velocidad, paradas, tipo de tecnología (MRL sin cuarto de máquinas, HYD económico, etc.) — nunca inventar cifras no confirmadas en `equipment_catalog.md`.
- La movilidad vertical resuelve problemas reales de espacio/accesibilidad/terreno (azoteas liberadas al no requerir cuarto de máquinas, accesibilidad universal, terrenos con desnivel) — no es solo "subir y bajar".
- Seguridad como ingeniería, no como advertencia — se transmite mostrando el componente/sistema real (amortiguadores, sensores), no con lenguaje de miedo.
- Qué NO decir: precios o promociones no confirmadas, comparaciones agresivas contra competidores específicos, superlativos sin dato que los respalde ("el mejor", "el más avanzado del mundo").

## Estilo visual
Basado en 16 piezas reales del equipo de marketing (`brand/reference_ads/`, no versionadas en git). Dos variantes conviven:

- **Variante "educativa/infografía"** (la más común): fondo blanco o azul marino claro, foto real de elevador/escalera eléctrica/estación a la derecha o de fondo, headline en azul marino oscuro (#0a2f5c aprox.) muy bold/condensado en mayúsculas, acentos en azul brillante (#1e5fd9 aprox.) para palabras clave dentro del cuerpo de texto, íconos circulares planos en azul con línea blanca (escudo, rayo, engrane, personas, casa, edificio, etc.), separador diagonal o curvo entre foto y texto, badge numerado ("01", "02"...) arriba a la derecha para series/carrusel. Fotografía realista de instalaciones (escaleras eléctricas en montañas/estaciones/zonas históricas, interiores de cabina).
- **Variante "producto premium"**: fondo azul marino casi negro (a veces negro puro), título en degradado dorado/bronce con efecto metálico 3D tipo revista técnica, líneas diagonales doradas finas de acento, producto real (amortiguador, tarjeta de control, sistema de estacionamiento) fotografiado en estudio con iluminación dramática (rim light dorado/azul). Mood aspiracional/high-end, no educativo.
- Ambas variantes comparten: logo "Elevadores ALAMEX" siempre arriba a la izquierda (versión blanca sobre fondo oscuro, versión azul/dorado original sobre fondo claro), URL `www.alam.mx` siempre en la esquina o barra inferior.
- **Cómo se resuelve el texto**: los modelos de generación de imagen no pueden escribir texto legible (se probó con Higgsfield y falla igual con cualquier proveedor — es una limitación de todos los modelos de difusión, no de uno en particular). Por eso el post final no le pide texto a la IA: la foto de fondo se genera vía IA (sin texto/paneles) y el texto se dibuja aparte con código real (`integrations/media/template_compositor.py`, fuentes `brand/fonts/`). Esto sí iguala la densidad de información real — no solo el mood fotográfico.
- **Layouts implementados** (el agente elige uno por post, y varía entre posts de la misma corrida — ver `agents/prompts/social_media_system.md`): `infografia` (la variante educativa de arriba, panel + bullets), `premium` (la variante producto premium de arriba, fondo oscuro/dorado, una sola idea), `hero` (foto a pantalla completa con headline superpuesto abajo — para statements cortos, no cubierto por ninguna de las dos variantes originales pero necesario para no repetir siempre el mismo layout).
- **Fotos reales de producto** (`brand/product_photos/`, ver su `README.md`): si hay una foto real que aplica al tema del post, el agente la usa en vez de generar una con IA — más auténtico y no gasta créditos. Hay 6 fotos reales registradas (máquina de tracción gearless MRL-L x3, bomba hidráulica HYD, botonera de piso LOP x2), ya retocadas (fondo de estudio + sombra, ver abajo) — se usan con `layout=premium` (fotos de producto aislado), no `infografia`/`hero`, que las recortarían mal.
- **Retoque de fotos reales — solo determinístico, nunca generativo**: se probó pasar una foto real por Higgsfield ("soul/reference", image-to-image) pidiendo "mejorarla" y el resultado cambió la forma real del producto y volvió a generar texto ilegible en la etiqueta — cualquier modelo generativo reintroduce el mismo problema que resolvimos con fotos reales en primer lugar, sin importar el `style_strength`. La única forma segura de "mejorar" una foto real es edición determinística que no redibuja nada: `integrations/media/product_retouch.py` usa `rembg` (segmentación, clasifica pixeles, no los inventa) para recortar el producto de su fondo original y lo compone sobre un fondo de estudio limpio con sombra — el producto queda pixel-por-pixel idéntico. **No conectar fotos reales a Higgsfield ni a ningún generador de imagen para "retocarlas."**
- Elementos obligatorios: el logo real se compone automáticamente sobre las imágenes generadas (pixel-perfecto; con un fondo blanco tipo "chip" detrás en los layouts de fondo oscuro para que siga siendo legible) — los agentes no deben describirlo en texto.

## Idioma
(pendiente) — por defecto, español neutro.

## Assets de marca
- `brand/logo_primary.png`: logotipo completo (wordmark "ALAMEX" con el isotipo circular integrado).
- `brand/logo_secondary.png`: isotipo solo (círculo azul/amarillo con la flecha).
