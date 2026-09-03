import base64
from unittest.mock import MagicMock, patch

from integrations.media.gemini import GeminiGenerator


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.gemini.requests.post")
def test_generate_image_text_only_decodes_inline_data(mock_post):
    encoded = base64.b64encode(b"fake-png-bytes").decode("ascii")
    mock_post.return_value = _mock_response(
        {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": encoded}}]}}]}
    )

    result = GeminiGenerator().generate_image("a red bicycle", aspect_ratio="1:1")

    assert result == b"fake-png-bytes"
    sent_parts = mock_post.call_args.kwargs["json"]["contents"][0]["parts"]
    assert len(sent_parts) == 1
    assert "a red bicycle" in sent_parts[0]["text"]
    assert mock_post.call_args.kwargs["headers"]["x-goog-api-key"] == "test-gemini-key"


@patch("integrations.media.gemini.requests.post")
def test_generate_image_with_reference_sends_inline_data_and_instructs_reuse(mock_post):
    encoded = base64.b64encode(b"fake-png-bytes").decode("ascii")
    mock_post.return_value = _mock_response(
        {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": encoded}}]}}]}
    )

    result = GeminiGenerator().generate_image("a red bicycle", reference_image=b"logo-bytes")

    assert result == b"fake-png-bytes"
    sent_parts = mock_post.call_args.kwargs["json"]["contents"][0]["parts"]
    assert len(sent_parts) == 2
    assert sent_parts[0]["inline_data"]["data"] == base64.b64encode(b"logo-bytes").decode("ascii")
    assert "attached logo" in sent_parts[1]["text"]
