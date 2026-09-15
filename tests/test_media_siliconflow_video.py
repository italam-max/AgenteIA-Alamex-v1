from unittest.mock import MagicMock, patch

import pytest

from integrations.media.siliconflow_video import SiliconFlowVideoGenerationFailed, SiliconFlowVideoGenerator


def _mock_response(json_data, content=None):
    response = MagicMock()
    response.json.return_value = json_data
    response.content = content
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media._common.time.sleep")
@patch("integrations.media.siliconflow_video.requests.get")
@patch("integrations.media.siliconflow_video.requests.post")
def test_generate_video_submits_polls_and_downloads(mock_post, mock_get, mock_sleep):
    mock_post.side_effect = [
        _mock_response({"requestId": "req-123"}),
        _mock_response({"status": "InProgress"}),
        _mock_response({"status": "Succeed", "results": {"videos": [{"url": "https://example.com/out.mp4"}]}}),
    ]
    mock_get.return_value = _mock_response({}, content=b"fake-mp4-bytes")

    result = SiliconFlowVideoGenerator().generate_video("a red bicycle riding by", aspect_ratio="9:16")

    assert result == b"fake-mp4-bytes"
    submit_call = mock_post.call_args_list[0]
    assert submit_call.args[0].endswith("/video/submit")
    assert submit_call.kwargs["json"]["prompt"] == "a red bicycle riding by"
    assert submit_call.kwargs["json"]["image_size"] == "720x1280"
    assert submit_call.kwargs["json"]["model"] == "Wan-AI/Wan2.2-T2V-A14B"

    status_call = mock_post.call_args_list[1]
    assert status_call.args[0].endswith("/video/status")
    assert status_call.kwargs["json"]["requestId"] == "req-123"


@patch("integrations.media._common.time.sleep")
@patch("integrations.media.siliconflow_video.requests.post")
def test_generate_video_raises_on_failed_status(mock_post, mock_sleep):
    # @retry re-runs the whole method (submit + poll) up to 3 times on any raised exception.
    mock_post.side_effect = [
        _mock_response({"requestId": "req-123"}),
        _mock_response({"status": "Failed", "reason": "boom"}),
    ] * 3

    with pytest.raises(SiliconFlowVideoGenerationFailed):
        SiliconFlowVideoGenerator().generate_video("a red bicycle")
