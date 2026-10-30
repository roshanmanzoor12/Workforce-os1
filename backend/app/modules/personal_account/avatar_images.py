"""Decode, orient and crop profile photos; serve the generated preset atlas."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000
PRESET_IDS = (
    "coral", "lavender", "sunshine", "mint",
    "sky", "aqua", "periwinkle", "rose",
    "sand", "ice", "apricot", "mauve",
)


def crop_profile_photo(data: bytes, zoom: float = 1, x: float = 0, y: float = 0) -> bytes:
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Choose a JPG, PNG or WebP photo smaller than 5 MB.")
    if not 1 <= zoom <= 3 or not -1 <= x <= 1 or not -1 <= y <= 1:
        raise ValueError("The crop position is invalid. Choose your photo again.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as original:
                if original.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Choose a JPG, PNG or WebP image.")
                if original.width * original.height > MAX_PIXELS:
                    raise ValueError("Choose a photo with fewer than 25 million pixels.")
                original.seek(0)  # A multi-frame input becomes a safe still photo.
                image = ImageOps.exif_transpose(original).convert("RGBA")
                edge = min(image.size) / zoom
                left = (image.width - edge) * (x + 1) / 2
                top = (image.height - edge) * (y + 1) / 2
                image = image.crop((round(left), round(top), round(left + edge), round(top + edge)))
                image = image.resize((512, 512), Image.Resampling.LANCZOS)
                output = BytesIO()
                # Re-encoding drops embedded metadata and ignores the supplied filename.
                image.save(output, "WEBP", quality=92, method=6)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("This image could not be opened. Try another JPG, PNG or WebP photo.") from exc


@lru_cache(maxsize=12)
def preset_image(preset_id: str) -> bytes:
    if preset_id not in PRESET_IDS:
        raise ValueError("Unknown avatar.")
    index = PRESET_IDS.index(preset_id)
    with Image.open(Path(__file__).with_name("assets") / "default-avatars.png") as atlas:
        # Integer boundaries also support atlas dimensions not divisible by 4 or 3.
        col, row = index % 4, index // 4
        tile = atlas.crop((round(col * atlas.width / 4), round(row * atlas.height / 3),
                           round((col + 1) * atlas.width / 4), round((row + 1) * atlas.height / 3)))
        output = BytesIO()
        tile.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS).save(
            output, "WEBP", quality=94, method=6)
        return output.getvalue()
