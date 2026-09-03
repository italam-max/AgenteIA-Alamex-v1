from unittest.mock import MagicMock, patch

import pytest

from agents.supervisor import supervisor_node


@patch("agents.supervisor.supabase_tools")
@patch("agents.supervisor.social_tools")
@patch("agents.supervisor.sonnet")
def test_llm_failure_marks_run_failed_instead_of_leaving_it_running(sonnet, social_tools, supabase_tools):
    social_tools.get_recent_posts.invoke.return_value = []
    social_tools.get_engagement_summary.invoke.return_value = {}
    supabase_tools.create_agent_run.invoke.return_value = 42

    broken_llm = MagicMock()
    broken_llm.with_structured_output.return_value.invoke.side_effect = RuntimeError("temperature not supported")
    sonnet.return_value = broken_llm

    with pytest.raises(RuntimeError):
        supervisor_node({"instruction": "encárgate de la publicidad de esta semana", "errors": []})

    supabase_tools.update_agent_run.invoke.assert_called_once()
    call_kwargs = supabase_tools.update_agent_run.invoke.call_args.args[0]
    assert call_kwargs["run_id"] == 42
    assert call_kwargs["status"] == "failed"
    assert "temperature not supported" in call_kwargs["error"]
