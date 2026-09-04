"""
Vista de solo lectura de lo que están haciendo los agentes. Corre localmente:
    streamlit run dashboard.py

Lee directo de Supabase con la service role key (nunca se expone al navegador,
esto corre server-side en tu máquina).
"""

import time
from datetime import datetime, timezone

import streamlit as st

from integrations.supabase_client import get_client

st.set_page_config(page_title="Agentes de Marketing", layout="wide")


@st.cache_data(ttl=15)
def load_runs(limit: int) -> list[dict]:
    result = (
        get_client()
        .table("agent_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@st.cache_data(ttl=3)
def load_latest_run() -> dict | None:
    """Short-TTL fetch used only by the live status banner, independent of the run list's
    cache — so the banner can refresh every few seconds without invalidating the tabs below."""
    result = get_client().table("agent_runs").select("*").order("started_at", desc=True).limit(1).execute()
    return result.data[0] if result.data else None


@st.cache_data(ttl=15)
def load_strategies(limit: int) -> list[dict]:
    result = (
        get_client()
        .table("weekly_strategy")
        .select("*")
        .order("week_start", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@st.cache_data(ttl=15)
def load_posts(limit: int) -> list[dict]:
    result = (
        get_client()
        .table("posts")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


STATUS_LABEL = {
    "completed": "Completado",
    "running": "En curso",
    "failed": "Falló",
    "published": "Publicado",
    "draft": "Borrador",
}
STATUS_ICON = {
    "completed": "✅",
    "running": "🟢",
    "failed": "🔴",
    "published": "✅",
    "draft": "⚪",
}
NODE_ICON = {
    "supervisor": "🧭",
    "social_media": "📣",
}


def _elapsed_since(iso_ts: str) -> str:
    started = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    seconds = int((datetime.now(timezone.utc) - started).total_seconds())
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}m {seconds}s"


def render_step_timeline(steps: list[dict]) -> None:
    for step in steps:
        icon = NODE_ICON.get(step.get("node"), "•")
        ts = (step.get("ts") or "")[11:19]  # HH:MM:SS out of the ISO timestamp
        st.markdown(f"`{ts}` {icon} **{step.get('node')}** — {step.get('message')}")
        if step.get("payload"):
            with st.expander("payload", expanded=False):
                st.json(step["payload"])


st.title("Agentes de Marketing")
st.caption("Estado de las corridas del Gerente de Marketing y el agente Social Media.")

with st.sidebar:
    st.header("Filtros")
    run_limit = st.slider("Corridas a mostrar", min_value=5, max_value=100, value=20)
    auto_refresh = st.checkbox("🔄 Auto-actualizar cada 5s", value=False)
    if st.button("Actualizar ahora"):
        st.cache_data.clear()

# --- Banner de estado en vivo ------------------------------------------------
latest_run = load_latest_run()
if latest_run and latest_run["status"] == "running":
    steps = latest_run.get("steps") or []
    last_step = steps[-1] if steps else None
    with st.container(border=True):
        st.markdown(f"### 🟢 Corriendo ahora — run #{latest_run['id']}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Instrucción", latest_run["instruction"][:40] + ("…" if len(latest_run["instruction"]) > 40 else ""))
        col2.metric("Nodo actual", NODE_ICON.get(last_step.get("node"), "") + " " + last_step.get("node") if last_step else "—")
        col3.metric("Corriendo desde hace", _elapsed_since(latest_run["started_at"]))
        if last_step:
            st.info(f"Último paso: {last_step.get('message')}")
        st.markdown("**Bitácora de esta corrida:**")
        render_step_timeline(steps[-8:])
elif latest_run:
    icon = STATUS_ICON.get(latest_run["status"], "⚪")
    st.caption(f"{icon} Última corrida: #{latest_run['id']} — {STATUS_LABEL.get(latest_run['status'], latest_run['status'])} — {latest_run.get('summary') or latest_run['instruction']}")
else:
    st.caption("Todavía no hay corridas registradas.")

runs = load_runs(run_limit)
strategies = load_strategies(run_limit)
posts = load_posts(run_limit * 5)

platforms = sorted({p["platform"] for p in posts}) if posts else []
selected_platforms = st.sidebar.multiselect("Plataforma", platforms, default=platforms)

tab_runs, tab_strategy, tab_posts = st.tabs(["Corridas", "Estrategia semanal", "Posts"])

with tab_runs:
    if not runs:
        st.info("Todavía no hay corridas registradas.")
    for run in runs:
        status = run["status"]
        icon = STATUS_ICON.get(status, "⚪")
        label = STATUS_LABEL.get(status, status)
        header = f"{icon} #{run['id']} — {run['instruction']} — {label} — {run['started_at']}"
        with st.expander(header, expanded=(status == "running")):
            col1, col2 = st.columns(2)
            col1.metric("Estado", f"{icon} {label}")
            col2.metric("Resumen", run.get("summary") or "-")
            if run.get("error"):
                st.error(run["error"])
            st.write("Modelos:", run.get("supervisor_model"), "/", run.get("social_media_model"))
            st.markdown("**Bitácora:**")
            render_step_timeline(run.get("steps") or [])

with tab_strategy:
    if not strategies:
        st.info("Todavía no hay estrategias registradas.")
    for strategy in strategies:
        st.subheader(f"Semana del {strategy['week_start']}")
        st.write(", ".join(strategy.get("themes") or []))
        st.write(strategy.get("rationale"))
        col1, col2 = st.columns(2)
        col1.metric("Posts planeados", strategy.get("num_posts"))
        col2.json(strategy.get("content_mix") or {})
        st.divider()

with tab_posts:
    filtered_posts = [p for p in posts if not selected_platforms or p["platform"] in selected_platforms]
    if not filtered_posts:
        st.info("Todavía no hay posts registrados.")
    columns = st.columns(3)
    for index, post in enumerate(filtered_posts):
        with columns[index % 3]:
            icon = STATUS_ICON.get(post["status"], "⚪")
            st.markdown(f"**{post['platform']}** · {icon} {STATUS_LABEL.get(post['status'], post['status'])}")
            if post.get("media_url") and post["post_type"] == "image":
                st.image(post["media_url"], use_container_width=True)
            elif post.get("media_url"):
                st.video(post["media_url"])
            st.caption(post.get("caption") or "")
            if post.get("permalink"):
                st.link_button("Ver publicación", post["permalink"])
            if post.get("error"):
                st.error(post["error"])
            st.divider()

if auto_refresh:
    time.sleep(5)
    st.rerun()
