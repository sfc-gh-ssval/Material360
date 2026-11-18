import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.snowflake import get_session, execute_query
from backend.services.extraction import extract_drawing
from backend.config import settings

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_and_extract(file: UploadFile = File(...)):
    """Upload a file to Snowflake stage and extract drawing data."""
    allowed_ext = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_ext:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {allowed_ext}")

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    content = await file.read()
    with open(tmp_path, "wb") as tmp:
        tmp.write(content)

    try:
        stage_fqn = f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.stage_name}"
        stage_path = f"@{stage_fqn}"
        session = get_session()
        session.file.put(f"file://{tmp_path}", stage_path, auto_compress=False, overwrite=True)
        session.sql(f"ALTER STAGE {stage_fqn} REFRESH").collect()

        result = extract_drawing(file.filename)
        return {"status": "success", "file_name": file.filename, "extraction": result}

    except Exception as e:
        raise HTTPException(500, f"Extraction failed: {str(e)}")
    finally:
        os.unlink(tmp_path)
