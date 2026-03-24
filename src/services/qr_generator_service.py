import base64
import io

import qrcode
from qrcode.image.pure import PyPNGImage


def generate_qr_base64(code: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)

    img = qr.make_image(image_factory=PyPNGImage)
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")
