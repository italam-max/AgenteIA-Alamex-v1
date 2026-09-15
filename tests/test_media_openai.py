import base64
from unittest.mock import MagicMock, patch

from integrations.media.openai import OpenAIGenerator


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.openai.requests.post")
def test_generate_image_text_only_calls_generations_endpoint(mock_post):
    encoded = base64.b64encode(b"fake-png-bytes").decode("ascii")
    mock_post.return_value = _mock_response({"data": [{"b64_json": encoded}]})

    result = OpenAIGenerator().generate_image("a red bicycle", aspect_ratio="1:1")

    assert result == b"fake-png-bytes"
    call = mock_post.call_args
    assert call.args[0].endswith("/images/generations")
    assert call.kwargs["json"]["prompt"] == "a red bicycle"
    assert call.kwargs["json"]["size"] == "1024x1024"
    assert call.kwargs["headers"]["Authorization"] == "Bearer test-openai-key"


@patch("integrations.media.openai.requests.post")
def test_generate_image_with_reference_calls_edits_endpoint(mock_post):
    encoded = base64.b64encode(b"fake-png-bytes").decode("ascii")
    mock_post.return_value = _mock_response({"data": [{"b64_json": encoded}]})

    result = OpenAIGenerator().generate_image("a red bicycle", aspect_ratio="16:9", reference_image=b"logo-bytes")

    assert result == b"fake-png-bytes"
    call = mock_post.call_args
    assert call.args[0].endswith("/images/edits")
    assert call.kwargs["data"]["size"] == "1536x1024"
    assert "attached logo" in call.kwargs["data"]["prompt"]
    assert call.kwargs["files"]["image"][1] == b"logo-bytes"
