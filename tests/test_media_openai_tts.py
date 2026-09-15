from unittest.mock import MagicMock, patch

import pytest

from integrations.media.openai_tts import OpenAITTSGenerationFailed, generate_speech


def _mock_response(content=b"", status_code=200):
    response = MagicMock()
    response.content = content
    response.status_code = status_code
    response.raise_for_status.return_value = None
    return response


@patch("integrations.media.openai_tts.requests.post")
def test_generate_speech_returns_audio_bytes(mock_post):
    mock_post.return_value = _mock_response(content=b"fake-mp3-bytes")

    result = generate_speech("hola, esto es una prueba")

    assert result == b"fake-mp3-bytes"
    call = mock_post.call_args
    assert call.args[0] == "https://api.openai.com/v1/audio/speech"
    assert call.kwargs["json"]["input"] == "hola, esto es una prueba"
    assert call.kwargs["json"]["model"] == "tts-1"
    assert call.kwargs["json"]["voice"] == "alloy"
    assert call.kwargs["headers"]["Authorization"] == "Bearer test-openai-key"


@patch("integrations.media.openai_tts.requests.post")
def test_generate_speech_raises_on_empty_response(mock_post):
    mock_post.return_value = _mock_response(content=b"")

    with pytest.raises(OpenAITTSGenerationFailed):
        generate_speech("hola")
