from unittest.mock import MagicMock, patch

from agents.graph import build_graph
from agents.schemas import PlannedPost, PostContent, VideoPostContent, WeeklyStrategy
from config.settings import settings


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
        planned_posts=[
            PlannedPost(type="image", content_type="producto", theme="lanzamiento", brief="Presentar la marca")
        ],
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
    assert save_post_call["content_type"] == "producto"
    assert save_post_call["layout"] == "infografia"
    assert save_post_call["reference_photo"] is None
    assert save_post_call["media_generator"] == settings.media_generator
    assert save_post_call["generation_prompt"] == "brand intro visual, on-brand colors"
    assert save_post_call["narration"] is None


@patch("agents.social_media.supabase_tools")
@patch("agents.social_media.social_tools")
@patch("agents.social_media.media_tools")
@patch("agents.social_media.sonnet")
@patch("agents.supervisor.supabase_tools")
@patch("agents.supervisor.social_tools")
@patch("agents.supervisor.sonnet")
def test_graph_happy_path_publishes_one_video_post(
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
        themes=["proceso de instalación"],
        num_posts=1,
        content_mix={"video": 1},
        rationale="Un vistazo breve al proceso funciona mejor en video que en imagen estática.",
        planned_posts=[
            PlannedPost(type="video", content_type="detras_de_camaras", theme="instalación", brief="Mostrar el proceso")
        ],
    )
    sup_sonnet.return_value = _fake_llm(strategy)

    sm_sonnet.return_value = _fake_llm(
        VideoPostContent(
            caption="Así se instala un MRL-L",
            video_prompt="technicians installing a gearless machine in an elevator shaft, brand colors",
            narration="En Alamex, instalar un MRL-L toma horas, no días, gracias a su diseño sin cuarto de máquinas.",
        )
    )
    sm_media_tools.generate_video.invoke.return_value = b"fake-mp4-bytes"
    sm_supabase_tools.upload_media.invoke.return_value = "https://example.supabase.co/storage/v1/object/public/post-media/x.mp4"
    sm_social_tools.publish_video_post.invoke.return_value = {
        "post_id": "123456_v1",
        "permalink": None,
        "caption": "Así se instala un MRL-L",
    }
    sm_supabase_tools.save_post.invoke.return_value = 6

    graph = build_graph()
    result = graph.invoke({"instruction": "encárgate de la publicidad de esta semana", "errors": []})

    assert result["published_posts"][0] == {"platform": "facebook", "post_row_id": 6, "post_id": "123456_v1"}
    assert result["errors"] == []

    sm_media_tools.generate_video.invoke.assert_called_once()
    sm_social_tools.publish_video_post.invoke.assert_called_once()
    sm_social_tools.publish_image_post.invoke.assert_not_called()

    save_post_call = sm_supabase_tools.save_post.invoke.call_args.args[0]
    assert save_post_call["post_type"] == "video"
    assert save_post_call["media_url"].endswith(".mp4")
    assert save_post_call["layout"] is None
    assert save_post_call["reference_photo"] is None
    assert save_post_call["media_generator"] == settings.video_generator
    assert save_post_call["generation_prompt"] == "technicians installing a gearless machine in an elevator shaft, brand colors"
    assert save_post_call["narration"] == "En Alamex, instalar un MRL-L toma horas, no días, gracias a su diseño sin cuarto de máquinas."
