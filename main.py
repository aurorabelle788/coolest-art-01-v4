"""coolest-art-01 v4 — "The Record Planet".

The artwork is a finished image bundled with this program. The program's
job is only to hand that image to the judge: read it, confirm it is a
valid JPEG inside the competition's size and dimension gates, and write
an exact copy to the output directory. No network, no randomness, no
extra files — the same bytes go in and the same bytes come out.
"""

from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path

# Competition gates for the artwork.
MAX_WIDTH = 1024
MAX_HEIGHT = 1024
MAX_BYTES = 1_048_576

BUNDLED_IMAGE = "entry.png"
OUTPUT_NAME = "entry.png"


def bundled_path() -> Path:
    """Path of the image shipped next to this program."""
    return Path(__file__).resolve().parent / BUNDLED_IMAGE


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) of a JPEG by walking its markers.

    Looks for the first Start-Of-Frame marker (baseline or progressive)
    and reads the dimensions stored there. Raises ValueError if the
    bytes are not a recognisable JPEG.
    """
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG: missing SOI marker")
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            raise ValueError("not a JPEG: bad marker prefix")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        seg_len = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
            return width, height
        pos += 2 + seg_len
    raise ValueError("not a JPEG: no SOF marker found")


def load_and_check() -> bytes:
    """Read the bundled image and enforce the competition gates."""
    path = bundled_path()
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError(f"image too large: {len(data)} bytes > {MAX_BYTES}")
    width, height = jpeg_dimensions(data)
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise ValueError(
            f"image too big: {width}x{height} > {MAX_WIDTH}x{MAX_HEIGHT}"
        )
    return data


def output_dir() -> Path:
    """Where the judge expects the artwork (env override, else /output)."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def main() -> int:
    data = load_and_check()
    width, height = jpeg_dimensions(data)
    dest = output_dir()
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / OUTPUT_NAME
    out.write_bytes(data)
    if out.read_bytes() != data:
        raise ValueError("output differs from bundled image")
    digest = hashlib.sha256(data).hexdigest()
    print(f"entry.png written: {width}x{height}, {len(data)} bytes, sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
