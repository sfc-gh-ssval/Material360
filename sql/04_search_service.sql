-- =============================================================================
-- 04_search_service.sql — Cortex Search over extracted drawings (Agent Chat)
-- Hybrid vector + keyword index on SEARCH_TEXT, embedded automatically with
-- snowflake-arctic-embed-m-v1.5. Other columns are returned / filterable.
-- Set WAREHOUSE to the warehouse you use (same as SNOWFLAKE_WAREHOUSE in .env).
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

CREATE CORTEX SEARCH SERVICE IF NOT EXISTS DRAWING_SEARCH
    ON SEARCH_TEXT
    ATTRIBUTES PART_NUMBER, PART_NAME, MATERIAL, FINISH, DRAWING_TYPE, SOURCE_LANGUAGE_NAME
    WAREHOUSE = MATERIAL360_WH
    TARGET_LAG = '1 hour'
    EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
AS (
    SELECT
        extraction_id,
        search_text,
        part_number,
        part_name,
        material,
        finish,
        drawing_type,
        source_language_name,
        file_name,
        revision,
        weight_kg,
        cosmetic_requirement,
        was_translated,
        original_part_name,
        original_finish,
        missing_fields::VARCHAR AS missing_fields_text,
        critical_dimensions::VARCHAR AS critical_dimensions_text,
        bom::VARCHAR AS bom_text,
        bbox_x,
        bbox_y,
        bbox_z,
        bbox_source
    FROM DRAWING_EXTRACTIONS
);
