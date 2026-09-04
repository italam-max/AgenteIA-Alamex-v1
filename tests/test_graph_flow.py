from unittest.mock import MagicMock, patch

from agents.graph import build_graph
from agents.schemas import PlannedPost, PostContent, WeeklyStrategy


def _fake_llm(structured_return):
    llm = MagicMock()
    llm.with_structured_output.return_value.invoke.return_value = structured_return
    return llm


@patch("agents.social_media.supabase_tools")
@patch("agents.social_media.social_tools")
@patch("agents.social_media.media_tools")
@patch("agents.social_media.sonnet")
@patch("agents.supervisor.supabase_tools")
@patch("agents.supervisor.social_tools")
@patch("agents.supervisor.sonnet")
def test_graph_happy_path_publishes_one_post(
    sup_sonnet,
    sup_social_tools,
    sup_supabase_tools,
    sm_sonnet,
    sm_media_tools,
    sm_social_tools,
    sm_supabase_tools,
):
    sup_social_tools.get_recent_posts.invoke.return_value = []
    sup_social_tools.get_engagement_summary.invoke.return_value = {}
    sup_supabase_tools.create_agent_run.invoke.return_value = 1
    sup_supabase_tools.save_weekly_strategy.invoke.return_value = 10

    strategy = WeeklyStrategy(
        themes=["lanzamiento"],
        num_posts=1,
        content_mix={"image": 1},
        rationale="Sin historial previo; se arranca con un post de introducción de marca.",
        planned_posts=[PlannedPost(type="image", theme="lanzamiento", brief="Presentar la marca")],
    )
    sup_sonnet.return_value = _fake_llm(strategy)

    sm_sonnet.return_value = _fake_llm(
        PostContent(
            caption="Conoce nuestra marca",
            media_prompt="brand intro visual, on-brand colors",
            headline="Conoce Alamex",
            bullets=[],
            image_alt_text="Fotografía de un elevador moderno en un edificio",
        )
    )
    sm_media_tools.generate_image.invoke.return_value = b"fake-png-bytes"
    sm_supabase_tools.upload_media.invoke.return_value = "https://example.supabase.co/storage/v1/object/public/post-media/x.png"
    sm_social_tools.publish_image_post.invoke.return_value = {
        "post_id": "123456_p1",
        "permalink": None,
        "caption": "Conoce nuestra marca",  # what was actually published, post-truncation
    }
    sm_supabase_tools.save_post.invoke.return_value = 5

    graph = build_graph()
    result = graph.invoke({"instruction": "encárgate de la publicidad de esta semana", "errors": []})

    assert result["run_id"] == 1
    assert result["strategy_id"] == 10
    assert len(result["published_posts"]) == 1
    assert result["published_posts"][0] == {"platform": "facebook", "post_row_id": 5, "post_id": "123456_p1"}
    assert result["errors"] == []

    sm_supabase_tools.update_agent_run.invoke.assert_called_once()
    assert sm_supabase_tools.update_agent_run.invoke.call_args.args[0]["status"] == "completed"

    save_post_call = sm_supabase_tools.save_post.invoke.call_args.args[0]
    assert save_post_call["caption"] == "Conoce nuestra marca"
