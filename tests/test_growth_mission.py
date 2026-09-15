from unittest.mock import MagicMock, patch

from agents.growth_mission import run_growth_tick
from agents.schemas import GrowthPlan, GrowthReply, PostContent, VideoPostContent
from config.settings import settings


def _fake_llm(structured_return):
    llm = MagicMock()
    llm.with_structured_output.return_value.invoke.return_value = structured_return
    return llm


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_returns_done_without_planning_once_target_reached(mock_get_publisher, mock_supabase_tools, mock_sonnet):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 150, "following_count": 20, "statuses_count": 30}
    mock_get_publisher.return_value = publisher

    result = run_growth_tick(target_followers=100)

    assert result == {"done": True, "followers_count": 150, "following_count": 20, "statuses_count": 30}
    mock_supabase_tools.save_growth_snapshot.invoke.assert_called_once()
    mock_sonnet.assert_not_called()
    publisher.get_notifications.assert_not_called()


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_clamps_replies_and_follows_to_configured_caps(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []

    plan = GrowthPlan(
        reasoning="Probar con varias respuestas y follows.",
        replies=[GrowthReply(status_id=f"status-{i}", text=f"Gracias {i}") for i in range(7)],
        accounts_to_follow=[f"acct-{i}" for i in range(8)],
        post_theme=None,
    )
    mock_sonnet.return_value = _fake_llm(plan)

    result = run_growth_tick(target_followers=100)

    # Defaults: GROWTH_MAX_REPLIES_PER_TICK=5, GROWTH_MAX_FOLLOWS_PER_TICK=5.
    assert publisher.reply_to_status.call_count == 5
    assert publisher.follow_account.call_count == 5
    assert result["replies"] == 5
    assert result["follows"] == 5
    assert result["posted"] is False


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_excludes_already_followed_accounts_from_candidates(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = [
        {"account_id": "already-followed", "username": "old_friend"},
        {"account_id": "new-account", "username": "new_friend"},
    ]
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = ["already-followed"]

    plan = GrowthPlan(reasoning="Nada que hacer.", replies=[], post_theme=None)
    mock_sonnet.return_value = _fake_llm(plan)

    run_growth_tick(target_followers=100)

    user_message = mock_sonnet.return_value.with_structured_output.return_value.invoke.call_args.args[0][1]
    assert "new-account" in user_message.content
    assert "already-followed" not in user_message.content


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_excludes_already_replied_mentions_from_notifications(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = [
        {"status_id": "already-replied", "account_id": "acct-1", "text": "hola"},
        {"status_id": "new-mention", "account_id": "acct-2", "text": "hey"},
    ]
    publisher.search_accounts_by_hashtag.return_value = []
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = ["already-replied"]

    plan = GrowthPlan(reasoning="Nada que hacer.", replies=[], post_theme=None)
    mock_sonnet.return_value = _fake_llm(plan)

    run_growth_tick(target_followers=100)

    user_message = mock_sonnet.return_value.with_structured_output.return_value.invoke.call_args.args[0][1]
    assert "new-mention" in user_message.content
    assert "already-replied" not in user_message.content


@patch("agents.growth_mission._generate_content")
@patch("agents.growth_mission.cached_system_message")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.media_tools")
@patch("agents.growth_mission.product_photos_tools")
@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_publishes_extra_post_when_plan_sets_a_theme(
    mock_get_publisher,
    mock_supabase_tools,
    mock_sonnet,
    mock_product_photos_tools,
    mock_media_tools,
    mock_social_tools,
    mock_cached_system_message,
    mock_generate_content,
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []
    mock_supabase_tools.create_agent_run.invoke.return_value = 99

    plan = GrowthPlan(
        reasoning="Vale la pena un post extra.", replies=[], post_theme="tema x", post_content_type="educativo"
    )
    mock_sonnet.return_value = _fake_llm(plan)

    mock_generate_content.return_value = PostContent(
        caption="Caption de prueba",
        media_prompt="prompt",
        headline="Titulo",
        bullets=[],
        image_alt_text="alt",
    )
    mock_media_tools.generate_image.invoke.return_value = b"fake-png-bytes"
    mock_supabase_tools.upload_media.invoke.return_value = "https://example.supabase.co/x.png"
    mock_social_tools.publish_image_post.invoke.return_value = {
        "post_id": "status-1",
        "permalink": "https://instance/@user/status-1",
        "caption": "Caption de prueba",
    }
    mock_supabase_tools.save_post.invoke.return_value = 7

    result = run_growth_tick(target_followers=100)

    assert result["posted"] is True
    mock_supabase_tools.save_post.invoke.assert_called_once()
    assert mock_supabase_tools.save_post.invoke.call_args.args[0]["content_type"] == "educativo"
    mock_supabase_tools.update_agent_run.invoke.assert_called_once_with(
        {"run_id": 99, "status": "completed", "summary": "Growth mission post: tema x"}
    )


@patch("agents.growth_mission._generate_content")
@patch("agents.growth_mission.cached_system_message")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.media_tools")
@patch("agents.growth_mission.product_photos_tools")
@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_publishes_extra_video_post_when_plan_sets_video_type(
    mock_get_publisher,
    mock_supabase_tools,
    mock_sonnet,
    mock_product_photos_tools,
    mock_media_tools,
    mock_social_tools,
    mock_cached_system_message,
    mock_generate_content,
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []
    mock_supabase_tools.create_agent_run.invoke.return_value = 99

    plan = GrowthPlan(
        reasoning="Vale la pena un post extra en video.",
        replies=[],
        post_theme="tema x",
        post_content_type="detras_de_camaras",
        post_type="video",
    )
    mock_sonnet.return_value = _fake_llm(plan)

    mock_generate_content.return_value = VideoPostContent(
        caption="Caption de prueba",
        video_prompt="prompt visual",
        narration="Guion de prueba para la voz narrada.",
    )
    mock_media_tools.generate_video.invoke.return_value = b"fake-mp4-bytes"
    mock_supabase_tools.upload_media.invoke.return_value = "https://example.supabase.co/x.mp4"
    mock_social_tools.publish_video_post.invoke.return_value = {
        "post_id": "status-1",
        "permalink": "https://instance/@user/status-1",
        "caption": "Caption de prueba",
    }
    mock_supabase_tools.save_post.invoke.return_value = 8

    result = run_growth_tick(target_followers=100)

    assert result["posted"] is True
    mock_media_tools.generate_video.invoke.assert_called_once()
    mock_social_tools.publish_video_post.invoke.assert_called_once()
    mock_social_tools.publish_image_post.invoke.assert_not_called()
    save_post_call = mock_supabase_tools.save_post.invoke.call_args.args[0]
    assert save_post_call["post_type"] == "video"
    assert save_post_call["media_generator"] == settings.video_generator
    assert save_post_call["generation_prompt"] == "prompt visual"
    assert save_post_call["narration"] == "Guion de prueba para la voz narrada."


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_records_engagement_snapshot_for_each_recent_post(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = [
        {
            "id": "status-1",
            "message": "Un post cualquiera",
            "created_at": "2026-09-07T00:00:00Z",
            "engagement": {"likes": 3, "comments": 1, "shares": 0},
            "impressions": None,
        }
    ]
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []

    plan = GrowthPlan(reasoning="Nada que hacer este ciclo.", replies=[], post_theme=None)
    mock_sonnet.return_value = _fake_llm(plan)

    run_growth_tick(target_followers=100)

    mock_supabase_tools.save_post_engagement_snapshot.invoke.assert_called_once_with(
        {
            "platform": "mastodon",
            "external_post_id": "status-1",
            "likes": 3,
            "comments": 1,
            "shares": 0,
            "impressions": None,
        }
    )


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_logs_failed_reply_and_still_processes_the_rest(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    publisher.reply_to_status.side_effect = [RuntimeError("Mastodon caído a medias"), None]
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []

    plan = GrowthPlan(
        reasoning="Dos respuestas, la primera fallará.",
        replies=[
            GrowthReply(status_id="status-1", text="Gracias 1"),
            GrowthReply(status_id="status-2", text="Gracias 2"),
        ],
        post_theme=None,
    )
    mock_sonnet.return_value = _fake_llm(plan)

    result = run_growth_tick(target_followers=100)

    # Both replies were attempted despite the first one failing mid-cycle — a partial API failure
    # doesn't abort the rest of the tick's actions.
    assert publisher.reply_to_status.call_count == 2
    assert result["replies"] == 2

    save_action_calls = [c.args[0] for c in mock_supabase_tools.save_growth_action.invoke.call_args_list]
    reply_calls = [c for c in save_action_calls if c["action_type"] == "reply"]
    assert len(reply_calls) == 2
    assert reply_calls[0]["target_status_id"] == "status-1"
    assert reply_calls[0]["result"] == "failed"
    assert "Mastodon caído a medias" in reply_calls[0]["error"]
    assert reply_calls[1]["target_status_id"] == "status-2"
    assert reply_calls[1]["result"] == "ok"


@patch("agents.growth_mission.sonnet")
@patch("agents.growth_mission.social_tools")
@patch("agents.growth_mission.supabase_tools")
@patch("agents.growth_mission.get_publisher")
def test_tick_logs_failed_follow_and_still_processes_the_rest(
    mock_get_publisher, mock_supabase_tools, mock_social_tools, mock_sonnet
):
    publisher = MagicMock()
    publisher.get_account_stats.return_value = {"followers_count": 10, "following_count": 5, "statuses_count": 3}
    publisher.get_notifications.return_value = []
    publisher.search_accounts_by_hashtag.return_value = []
    publisher.follow_account.side_effect = [RuntimeError("rate limited"), None]
    mock_get_publisher.return_value = publisher

    mock_social_tools.get_recent_posts.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_snapshots.invoke.return_value = []
    mock_supabase_tools.get_recent_growth_actions.invoke.return_value = []
    mock_supabase_tools.get_replied_status_ids.invoke.return_value = []
    mock_supabase_tools.get_followed_account_ids.invoke.return_value = []

    plan = GrowthPlan(
        reasoning="Dos follows, el primero fallará.",
        replies=[],
        accounts_to_follow=["acct-1", "acct-2"],
        post_theme=None,
    )
    mock_sonnet.return_value = _fake_llm(plan)

    result = run_growth_tick(target_followers=100)

    assert publisher.follow_account.call_count == 2
    assert result["follows"] == 2

    save_action_calls = [c.args[0] for c in mock_supabase_tools.save_growth_action.invoke.call_args_list]
    follow_calls = [c for c in save_action_calls if c["action_type"] == "follow"]
    assert len(follow_calls) == 2
    assert follow_calls[0]["target_account_id"] == "acct-1"
    assert follow_calls[0]["result"] == "failed"
    assert "rate limited" in follow_calls[0]["error"]
    assert follow_calls[1]["target_account_id"] == "acct-2"
    assert follow_calls[1]["result"] == "ok"
