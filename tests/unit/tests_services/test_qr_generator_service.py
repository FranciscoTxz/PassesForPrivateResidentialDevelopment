import base64
import io
from unittest.mock import MagicMock, patch

from services.qr_generator_service import generate_qr


class TestGenerateQrBase64:
    def test_returns_string(self):
        result = generate_qr("test-code")

        assert isinstance(result, str)

    def test_generate_png_bytes(self):
        result = generate_qr("test-code", png_image=True)

        assert isinstance(result, bytes)
        assert result[:4] == b"\x89PNG"

    def test_result_is_valid_base64(self):
        result = generate_qr("test-code")

        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_different_codes_produce_different_qrs(self):
        result_a = generate_qr("code-A")
        result_b = generate_qr("code-B")

        assert result_a != result_b

    def test_same_code_produces_same_qr(self):
        result_a = generate_qr("stable-code")
        result_b = generate_qr("stable-code")

        assert result_a == result_b

    def test_output_is_png_bytes(self):
        result = generate_qr("ping")

        raw = base64.b64decode(result)
        # PNG magic bytes: \x89PNG
        assert raw[:4] == b"\x89PNG"

    def test_uses_bytesio_buffer(self):
        real_bytesio_class = io.BytesIO

        with patch("services.qr_generator_service.io.BytesIO") as mock_bytesio_class:
            mock_buf = MagicMock(wraps=real_bytesio_class())
            mock_bytesio_class.return_value: MagicMock = mock_buf

            generate_qr("buffer-test")

        mock_buf.seek.assert_called_once_with(0)
        mock_buf.read.assert_called_once()
