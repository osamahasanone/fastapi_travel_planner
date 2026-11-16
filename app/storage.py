from pathlib import Path

import filetype

UPLOAD_DIR = Path("uploads")
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024  # 5 MB

# Allowed media types -> file extension on disk
EXTENSIONS: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}


def detect_type(data: bytes) -> tuple[str, str] | None:
    """
    Return (media type, extension) from the file's real
    first bytes, or None if not allowed.
    """
    kind = filetype.guess(data)
    if kind is None or kind.mime not in EXTENSIONS:
        return None
    return kind.mime, EXTENSIONS[kind.mime]


def document_path(trip_id: int, document_id: int, extension: str) -> Path:
    """
    Where a document lives on disk.
    Built from ids only, never from the client's filename.
    """
    return UPLOAD_DIR / str(trip_id) / f"{document_id}{extension}"


def save_document(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
