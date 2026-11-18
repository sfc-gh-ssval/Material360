import json
from fastapi import APIRouter, HTTPException, Query
from backend.services.snowflake import execute_query

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/extractions")
def list_extractions(
    language: str = None,
    has_missing: bool = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """List all drawing extractions with optional filters."""
    where_clauses = []
    if language:
        where_clauses.append(f"source_language_name = '{language}'")
    if has_missing is True:
        where_clauses.append("ARRAY_SIZE(missing_fields) > 0")
    elif has_missing is False:
        where_clauses.append("(ARRAY_SIZE(missing_fields) = 0 OR missing_fields IS NULL)")

    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    sql = f"""
    SELECT extraction_id, file_name, part_number, part_name, original_part_name,
           revision, material, finish, original_finish, cosmetic_requirement,
           designer, draftsman,
           source_language, source_language_name, was_translated, weight_kg,
           bbox_x, bbox_y, bbox_z, bbox_source,
           missing_fields, critical_dimensions, bom, original_bom,
           extraction_timestamp
    FROM DRAWING_EXTRACTIONS
    {where_sql}
    ORDER BY extraction_timestamp DESC
    LIMIT {limit} OFFSET {offset}
    """
    rows = execute_query(sql)
    # Convert VARIANT columns from strings
    for row in rows:
        for col in ["MISSING_FIELDS", "CRITICAL_DIMENSIONS", "BOM", "ORIGINAL_BOM"]:
            if col in row and isinstance(row[col], str):
                try:
                    row[col] = json.loads(row[col])
                except (json.JSONDecodeError, TypeError):
                    pass
    return {"extractions": rows, "count": len(rows)}


@router.get("/extractions/{extraction_id}")
def get_extraction(extraction_id: str):
    """Get a single extraction by ID."""
    rows = execute_query(
        "SELECT * FROM DRAWING_EXTRACTIONS WHERE extraction_id = %s",
        (extraction_id,),
    )
    if not rows:
        raise HTTPException(404, "Extraction not found")
    row = rows[0]
    for col in ["MISSING_FIELDS", "CRITICAL_DIMENSIONS", "BOM", "ORIGINAL_BOM", "PARSED"]:
        if col in row and isinstance(row[col], str):
            try:
                row[col] = json.loads(row[col])
            except (json.JSONDecodeError, TypeError):
                pass
    return row


@router.get("/reconciliation")
def get_reconciliation():
    """Get BOM reconciliation data."""
    sql = """
    SELECT part_number, part_name, source_language_name,
           drawing_material, bom_material, reconciled_material, material_source,
           drawing_finish, bom_finish, reconciled_finish, finish_source,
           file_name
    FROM V_BOM_RECONCILIATION
    ORDER BY part_number
    """
    return {"reconciliation": execute_query(sql)}


@router.get("/bom")
def list_bom():
    """List all BOM entries."""
    return {"bom": execute_query("SELECT * FROM BOM_PARTS ORDER BY part_number")}
