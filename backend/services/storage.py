"""封装文件存储读写与上传资源落盘逻辑。"""

import mimetypes
import uuid
from pathlib import Path

from fastapi import UploadFile


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    return name.replace("\\", "_").replace("/", "_")


def get_uploads_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "uploads"


async def save_upload_file(file: UploadFile) -> dict:
    uploads_dir = get_uploads_dir()
    uploads_dir.mkdir(parents=True, exist_ok=True)

    original_name = _safe_filename(file.filename or "file")
    uid = uuid.uuid4().hex
    ext = Path(original_name).suffix
    stored_name = f"{uid}{ext}"
    stored_path = uploads_dir / stored_name

    content = await file.read()
    stored_path.write_bytes(content)

    mime_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
    return {
        "stored_path": str(stored_path),
        "stored_name": stored_name,
        "original_name": original_name,
        "mime_type": mime_type,
        "size": len(content),
    }
