"""
Valida cada integración por separado antes de correr el flujo completo (main.py).
Uso: python scripts/smoke_test.py [--publish]

Sin --publish, prueba Supabase y la lectura de cada red social habilitada, pero NO
genera imagen ni publica (la primera generación descarga el modelo, puede tardar
varios minutos). Con --publish, además genera 1 imagen local y la publica en cada
plataforma listada en ENABLED_PLATFORMS.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from integrations.media.registry import get_generator
from integrations.social.registry import get_publisher
from integrations.supabase_client import get_client


def check_supabase() -> None:
    get_client().table("agent_runs").select("id").limit(1).execute()
    print("[OK] Supabase: conexión y tabla agent_runs accesibles")


def check_platform_read(platform: str) -> None:
    get_publisher(platform).get_engagement_summary()
    print(f"[OK] {platform}: lectura de engagement/insights exitosa")


def check_local_generation() -> bytes:
    image_bytes = get_generator(settings.media_generator).generate_image("A simple test image, plain background")
    print(f"[OK] Generación local: imagen generada ({len(image_bytes)} bytes)")
    return image_bytes


def check_platform_publish(platform: str, image_bytes: bytes) -> None:
    result = get_publisher(platform).publish_image(image_bytes, "Smoke test post")
    print(f"[OK] {platform}: publicación exitosa -> {result}")


def main() -> None:
    publish = "--publish" in sys.argv

    check_supabase()
    for platform in settings.enabled_platforms:
        check_platform_read(platform)

    if publish:
        image_bytes = check_local_generation()
        for platform in settings.enabled_platforms:
            check_platform_publish(platform, image_bytes)
    else:
        print("(omitido: generación local + publicación real. Usa --publish para probarlas)")

    print("\nTodo listo.")


if __name__ == "__main__":
    main()
