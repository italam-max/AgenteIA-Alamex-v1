import time
from datetime import datetime

from agents.growth_mission import run_growth_tick
from config.settings import settings


def main() -> None:
    print(
        f"Misión de crecimiento (Mastodon) — objetivo: {settings.growth_target_followers} seguidores, "
        f"ciclo cada {settings.growth_tick_minutes} min. Ctrl+C para detener.\n"
    )
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = run_growth_tick(settings.growth_target_followers)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive across a transient failure
            print(f"[{now}] Ciclo falló: {exc}")
        else:
            if result["done"]:
                print(f"[{now}] Objetivo alcanzado: {result['followers_count']} seguidores. Deteniendo.")
                return
            print(
                f"[{now}] {result['followers_count']} seguidores "
                f"(+{result['replies']} respuestas, +{result['follows']} follows, "
                f"post extra: {'sí' if result['posted'] else 'no'})"
            )

        time.sleep(settings.growth_tick_minutes * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDetenido por el usuario.")
