from unittest.mock import MagicMock, patch

from agents.schemas import PostContent
from post_now import create_single_post


def _fake_llm(structured_return):
    llm = MagicMock()
    llm.with_structured_output.return_value.invoke.return_value = structured_return
    return llm


@patch("post_now.supabase_tools")
@patch("agents.social_media.supabase_tools")
@patch("agents.social_media.social_tools")
@patch("agents.social_media.media_tools")
@patch("agents.social_media.sonnet")
def test_create_single_post_skips_weekly_strategy_and_publishes_one_post(
    sm_sonnet, sm_media_tools, sm_social_tools, sm_supabase_tools, pn_supabase_tools
):
    pn_supabase_tools.create_agent_run.invoke.return_value = 1
    pn_supabase_tools.save_weekly_strategy.invoke.return_value = 10

    sm_sonnet.return_value = _fake_llm(
        PostContent(
            caption="La máquina que mueve al MRL-L",
            media_prompt="unused",
            headline="Tracción gearless",
            bullets=[],
            layout="premium",
            reference_photo="mrl_maquina_traccion_gearless_1.png",
            image_alt_text="Máquina de tracción gearless azul en fondo de estudio",
        )
    )
    sm_media_tools.generate_image.invoke.return_value = b"fake-png-bytes"
    sm_supabase_tools.upload_media.invoke.return_value = "https://example.supabase.co/x.png"
    sm_social_tools.publish_image_post.invoke.return_value = {
        "post_id": "1",
        "permalink": "https://mastodon.social/@x/1",
        "caption": "La máquina que mueve al MRL-L",
    }
    sm_supabase_tools.save_post.invoke.return_value = 5

    result = create_single_post("la máquina gearless del MRL-L")

    pn_supabase_tools.create_agent_run.invoke.assert_called_once()
    pn_supabase_tools.save_weekly_strategy.invoke.assert_called_once()
    assert pn_supabase_tools.save_weekly_strategy.invoke.call_args.args[0]["num_posts"] == 1

    assert result["run_id"] == 1
    assert len(result["published_posts"]) == 1
    assert result["errors"] == []
