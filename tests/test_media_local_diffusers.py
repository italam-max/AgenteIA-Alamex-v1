from unittest.mock import MagicMock, patch

from integrations.media.local_diffusers import LocalDiffusersGenerator


@patch("integrations.media.local_diffusers.StableDiffusionPipeline")
def test_generate_image_returns_png_bytes_and_caches_pipeline(mock_pipeline_cls):
    fake_image = MagicMock()
    fake_image.save.side_effect = lambda buffer, format: buffer.write(b"fake-png-bytes")

    fake_pipe = MagicMock()
    fake_pipe.to.return_value = fake_pipe
    fake_pipe.return_value = MagicMock(images=[fake_image])
    mock_pipeline_cls.from_pretrained.return_value = fake_pipe

    generator = LocalDiffusersGenerator()
    result = generator.generate_image("a red bicycle", aspect_ratio="1:1")

    assert result == b"fake-png-bytes"
    fake_pipe.assert_called_once()
    call_kwargs = fake_pipe.call_args.kwargs
    assert call_kwargs["prompt"] == "a red bicycle"
    assert call_kwargs["width"] == 512
    assert call_kwargs["height"] == 512

    # A second call must reuse the already-loaded pipeline instead of reloading it.
    generator.generate_image("another prompt")
    mock_pipeline_cls.from_pretrained.assert_called_once()
