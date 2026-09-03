"""
Vista de solo lectura de lo que están haciendo los agentes. Corre localmente:
    streamlit run dashboard.py

Lee directo de Supabase con la service role key (nunca se expone al navegador,
esto corre server-side en tu máquina).
"""

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

st.title("Agentes de Marketing")
st.caption("Estado de las corridas del Gerente de Marketing y el agente Social Media.")

with st.sidebar:
    st.header("Filtros")
    run_limit = st.slider("Corridas a mostrar", min_value=5, max_value=100, value=20)
    if st.button("Actualizar"):
        st.cache_data.clear()

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
        status = STATUS_LABEL.get(run["status"], run["status"])
        with st.expander(f"#{run['id']} — {run['instruction']} — {status} — {run['started_at']}"):
            col1, col2 = st.columns(2)
            col1.metric("Estado", status)
            col2.metric("Resumen", run.get("summary") or "-")
            if run.get("error"):
                st.error(run["error"])
            st.write("Modelos:", run.get("supervisor_model"), "/", run.get("social_media_model"))
            st.write("Pasos:")
            for step in run.get("steps") or []:
                st.text(f"[{step.get('ts')}] ({step.get('node')}) {step.get('message')}")
                if step.get("payload"):
                    st.json(step["payload"])

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
            st.markdown(f"**{post['platform']}** · {STATUS_LABEL.get(post['status'], post['status'])}")
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
