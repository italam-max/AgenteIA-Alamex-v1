"""
Publica UN post ahora mismo, sin pasar por el ciclo de planeación semanal del supervisor
(no analiza engagement ni decide cuántos posts hacer — eso es main.py). Útil para pruebas
rápidas o cuando ya sabes exactamente qué quieres publicar.

Uso:
    python post_now.py "tema o brief del post (ej. la máquina gearless del MRL-L)"
    python post_now.py "tema o brief del post" --video   # genera un post de video en vez de imagen
    python post_now.py "brief" --content-type refacciones   # prueba un content_type distinto a "producto"
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.schemas import PlannedPost
from agents.social_media import social_media_node
from tools import supabase_tools

SOCIAL_MEDIA_MODEL = "claude-sonnet-5"


def create_single_post(brief: str, post_type: str = "image", content_type: str = "producto") -> dict:
    run_id = supabase_tools.create_agent_run.invoke(
        {
            "instruction": f"Publicación puntual: {brief}",
            "supervisor_model": "n/a (post_now.py salta la planeación semanal)",
            "social_media_model": SOCIAL_MEDIA_MODEL,
        }
    )
    strategy_id = supabase_tools.save_weekly_strategy.invoke(
        {
            "run_id": run_id,
            "week_start": date.today().isoformat(),
            "themes": [brief],
            "num_posts": 1,
            "content_mix": {post_type: 1},
            "rationale": (
                "Publicación puntual fuera del ciclo semanal — se generó un solo post a demanda, "
                "sin analizar desempeño histórico ni decidir una estrategia de la semana."
            ),
        }
    )

    state = {
        "run_id": run_id,
        "strategy_id": strategy_id,
        "planned_posts": [PlannedPost(type=post_type, content_type=content_type, theme=brief, brief=brief).model_dump()],
        "errors": [],
    }
    result = social_media_node(state)
    return {"run_id": run_id, **result}


def main() -> None:
    args = sys.argv[1:]
    video = "--video" in args
    args = [a for a in args if a != "--video"]

    content_type = "producto"
    if "--content-type" in args:
        flag_index = args.index("--content-type")
        try:
            content_type = args[flag_index + 1]
        except IndexError:
            print("Uso: --content-type requiere un valor, ej. --content-type refacciones")
            sys.exit(1)
        args = args[:flag_index] + args[flag_index + 2 :]

    if not args:
        print('Uso: python post_now.py "tema o brief del post" [--video] [--content-type <tipo>]')
        sys.exit(1)

    result = create_single_post(args[0], post_type="video" if video else "image", content_type=content_type)

    print(f"\nRun id: {result['run_id']}")
    print(f"Posts publicados: {len(result.get('published_posts', []))}/1")
    if result.get("errors"):
        print(f"Errores: {result['errors']}")


if __name__ == "__main__":
    main()
