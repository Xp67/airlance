from io import BytesIO
import os
from typing import Tuple
from PIL import Image, UnidentifiedImageError  # type: ignore


def process_image(file_bytes: bytes, filename: str) -> Tuple[Image.Image, BytesIO, str, str, bool]:
    """Open image bytes and ensure the file is JPEG or PNG.

    If the original format is neither JPEG nor PNG, the image is converted to
    JPEG. Returns a tuple with:
    - the PIL Image object in RGB mode
    - a BytesIO buffer containing the (possibly converted) original image data
    - the (possibly updated) filename
    - the corresponding MIME content type
    - a boolean indicating whether a conversion was performed
    """
    img = Image.open(BytesIO(file_bytes))
    image = img.convert("RGB")
    original_format = img.format

    if original_format not in ("JPEG", "PNG"):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=100)
        buffer.seek(0)
        new_filename = os.path.splitext(filename)[0] + ".jpg"
        return image, buffer, new_filename, "image/jpeg", True
    else:
        buffer = BytesIO(file_bytes)
        buffer.seek(0)
        content_type = "image/jpeg" if original_format == "JPEG" else "image/png"
        return image, buffer, filename, content_type, False
