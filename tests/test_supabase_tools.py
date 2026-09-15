from unittest.mock import MagicMock, patch

from tools.supabase_tools import (
    append_run_step,
    get_followed_account_ids,
    get_post_engagement_history,
    get_recent_growth_actions,
    get_recent_growth_snapshots,
    get_replied_status_ids,
    save_growth_action,
    save_growth_snapshot,
    save_post_engagement_snapshot,
)


@patch("tools.supabase_tools.get_client")
def test_append_run_step_calls_atomic_rpc_instead_of_read_modify_write(mock_get_client):
    client = MagicMock()
    mock_get_client.return_value = client

    append_run_step.invoke({"run_id": 1, "node": "social_media", "message": "generó la imagen", "payload": {"a": 1}})

    client.table.assert_not_called()
    client.rpc.assert_called_once()
    rpc_name, rpc_params = client.rpc.call_args.args
    assert rpc_name == "append_run_step"
    assert rpc_params["p_run_id"] == 1
    step = rpc_params["p_step"]
    assert step["node"] == "social_media"
    assert step["message"] == "generó la imagen"
    assert step["payload"] == {"a": 1}
    assert isinstance(step["ts"], str)
    client.rpc.return_value.execute.assert_called_once()


@patch("tools.supabase_tools.get_client")
def test_save_growth_snapshot_inserts_row_and_returns_id(mock_get_client):
    mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": 7}]

    row_id = save_growth_snapshot.invoke(
        {"platform": "mastodon", "followers_count": 42, "following_count": 10, "statuses_count": 5}
    )

    assert row_id == 7
    insert_call = mock_get_client.return_value.table.return_value.insert.call_args.args[0]
    assert insert_call == {
        "platform": "mastodon",
        "followers_count": 42,
        "following_count": 10,
        "statuses_count": 5,
    }


@patch("tools.supabase_tools.get_client")
def test_save_growth_action_inserts_row_and_returns_id(mock_get_client):
    mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": 3}]

    row_id = save_growth_action.invoke(
        {
            "platform": "mastodon",
            "action_type": "follow",
            "target_account_id": "acct-1",
            "rationale": "relevante al giro",
            "result": "ok",
        }
    )

    assert row_id == 3
    insert_call = mock_get_client.return_value.table.return_value.insert.call_args.args[0]
    assert insert_call["action_type"] == "follow"
    assert insert_call["target_account_id"] == "acct-1"
    assert insert_call["result"] == "ok"


@patch("tools.supabase_tools.get_client")
def test_get_recent_growth_snapshots_returns_oldest_first(mock_get_client):
    newest_first = [{"id": 2, "recorded_at": "2026-09-02"}, {"id": 1, "recorded_at": "2026-09-01"}]
    (
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data
    ) = newest_first

    result = get_recent_growth_snapshots.invoke({"platform": "mastodon"})

    assert [row["id"] for row in result] == [1, 2]


@patch("tools.supabase_tools.get_client")
def test_get_recent_growth_actions_returns_oldest_first(mock_get_client):
    newest_first = [{"id": 20}, {"id": 10}]
    (
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data
    ) = newest_first

    result = get_recent_growth_actions.invoke({"platform": "mastodon"})

    assert [row["id"] for row in result] == [10, 20]


@patch("tools.supabase_tools.get_client")
def test_get_followed_account_ids_returns_distinct_sorted_ids_ignoring_nulls(mock_get_client):
    rows = [
        {"target_account_id": "acct-b"},
        {"target_account_id": "acct-a"},
        {"target_account_id": "acct-a"},
        {"target_account_id": None},
    ]
    (
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data
    ) = rows

    result = get_followed_account_ids.invoke({"platform": "mastodon"})

    assert result == ["acct-a", "acct-b"]
    select_mock = mock_get_client.return_value.table.return_value.select.return_value
    assert select_mock.eq.call_args.args == ("platform", "mastodon")
    assert select_mock.eq.return_value.eq.call_args.args == ("action_type", "follow")
    assert select_mock.eq.return_value.eq.return_value.eq.call_args.args == ("result", "ok")


@patch("tools.supabase_tools.get_client")
def test_get_replied_status_ids_filters_by_reply_action_type_and_ok_result(mock_get_client):
    rows = [{"target_status_id": "status-2"}, {"target_status_id": "status-1"}, {"target_status_id": None}]
    (
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data
    ) = rows

    result = get_replied_status_ids.invoke({"platform": "mastodon"})

    assert result == ["status-1", "status-2"]
    select_mock = mock_get_client.return_value.table.return_value.select.return_value
    assert select_mock.eq.call_args.args == ("platform", "mastodon")
    assert select_mock.eq.return_value.eq.call_args.args == ("action_type", "reply")
    assert select_mock.eq.return_value.eq.return_value.eq.call_args.args == ("result", "ok")


@patch("tools.supabase_tools.get_client")
def test_save_post_engagement_snapshot_inserts_row_and_returns_id(mock_get_client):
    mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [{"id": 55}]

    row_id = save_post_engagement_snapshot.invoke(
        {"platform": "mastodon", "external_post_id": "status-1", "likes": 3, "comments": 1, "shares": 0}
    )

    assert row_id == 55
    insert_call = mock_get_client.return_value.table.return_value.insert.call_args.args[0]
    assert insert_call["external_post_id"] == "status-1"
    assert insert_call["impressions"] is None


@patch("tools.supabase_tools.get_client")
def test_get_post_engagement_history_returns_all_snapshots_oldest_first(mock_get_client):
    snapshots = [{"recorded_at": "2026-09-01", "likes": 1}, {"recorded_at": "2026-09-02", "likes": 4}]
    (
        mock_get_client.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data
    ) = snapshots

    result = get_post_engagement_history.invoke({"platform": "mastodon", "external_post_id": "status-1"})

    assert result == snapshots
