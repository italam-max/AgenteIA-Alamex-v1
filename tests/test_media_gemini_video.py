from unittest.mock import MagicMock, patch

import pytest

from integrations.media.gemini_video import GeminiVideoGenerationFailed, GeminiVideoGenerator


def _mock_response(json_data, status_code=200, content=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.content = content
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media._common.time.sleep")
@patch("integrations.media.gemini_video.requests.get")
@patch("integrations.media.gemini_video.requests.post")
def test_generate_video_submits_polls_and_downloads(mock_post, mock_get, mock_sleep):
    mock_post.return_value = _mock_response({"name": "operations/abc123"})
    mock_get.side_effect = [
        _mock_response({"done": False}),
        _mock_response(
            {
                "done": True,
                "response": {
                    "generateVideoResponse": {
                        "generatedSamples": [{"video": {"uri": "https://example.com/out.mp4"}}]
                    }
                },
            }
        ),
        _mock_response({}, content=b"fake-mp4-bytes"),
    ]

    result = GeminiVideoGenerator().generate_video("a red bicycle riding by", aspect_ratio="9:16")

    assert result == b"fake-mp4-bytes"
    submit_call = mock_post.call_args
    assert submit_call.kwargs["json"]["instances"][0]["prompt"] == "a red bicycle riding by"
    assert submit_call.kwargs["json"]["parameters"]["aspectRatio"] == "9:16"
    assert "veo-3.1-fast-generate-preview" in submit_call.args[0]


@patch("integrations.media._common.time.sleep")
@patch("integrations.media.gemini_video.requests.get")
@patch("integrations.media.gemini_video.requests.post")
def test_generate_video_raises_on_operation_error(mock_post, mock_get, mock_sleep):
    mock_post.return_value = _mock_response({"name": "operations/abc123"})
    mock_get.return_value = _mock_response({"done": True, "error": {"message": "boom"}})

    with pytest.raises(GeminiVideoGenerationFailed):
        GeminiVideoGenerator().generate_video("a red bicycle")
