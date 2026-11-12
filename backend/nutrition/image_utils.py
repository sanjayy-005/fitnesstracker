import io

from PIL import Image, UnidentifiedImageError

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 5 * 1024 * 1024


def normalize_meal_image(file_obj, *, max_px: int) -> tuple[bytes, str]:
    """Resize, strip EXIF, and re-encode as JPEG."""
    raw = file_obj.read()
    if len(raw) > MAX_BYTES:
        raise ValueError("Image must be 5 MB or smaller.")
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except UnidentifiedImageError as exc:
        raise ValueError("Upload a JPEG, PNG or WebP image.") from exc

    mime = Image.MIME.get(image.format)
    if mime not in ALLOWED_MIME:
        raise ValueError("Upload a JPEG, PNG or WebP image.")

    image = image.convert("RGB")
    image.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=85, optimize=True)
    return out.getvalue(), "image/jpeg"
