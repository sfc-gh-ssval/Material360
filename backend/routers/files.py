import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.services.snowflake import get_session
from backend.config import settings

router = APIRouter(prefix="/api", tags=["files"])

MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}


@router.get("/files/{filename}/preview")
def preview_file(filename: str):
    """Download from stage and serve inline for browser viewing."""
    stage_fqn = f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.stage_name}"

    ext = os.path.splitext(filename)[1].lower()
    media_type = MIME_MAP.get(ext, "application/octet-stream")

    try:
        session = get_session()
        tmp_dir = tempfile.mkdtemp()
        session.file.get(f"@{stage_fqn}/{filename}", tmp_dir)

        local_path = os.path.join(tmp_dir, filename)
        if not os.path.exists(local_path):
            raise HTTPException(404, f"File not found on stage: {filename}")

        return FileResponse(
            path=local_path,
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename=\"{filename}\""},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get file: {str(e)}")
