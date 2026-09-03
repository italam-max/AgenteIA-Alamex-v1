import sys

from agents.graph import build_graph


def main() -> None:
    if len(sys.argv) < 2:
        print('Uso: python main.py "encárgate de la publicidad de esta semana"')
        sys.exit(1)

    instruction = sys.argv[1]
    graph = build_graph()
    result = graph.invoke({"instruction": instruction, "errors": []})

    print(f"\nRun id: {result.get('run_id')}")
    print(f"Estrategia: {result.get('strategy', {}).get('rationale')}")
    print(f"Posts publicados: {len(result.get('published_posts', []))}/{len(result.get('planned_posts', []))}")
    if result.get("errors"):
        print(f"Errores: {result['errors']}")


if __name__ == "__main__":
    main()
