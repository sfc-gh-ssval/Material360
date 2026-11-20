-- =============================================================================
-- 02_views.sql — BOM reconciliation (single source of truth)
-- Resolved value = drawing value, else BOM value.
-- Source: 'From drawing' | 'Filled from BOM' | 'MISSING'.
-- Note: when both are present and differ, the drawing value wins (no conflict flag).
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

CREATE OR REPLACE VIEW V_BOM_RECONCILIATION AS
SELECT
    e.extraction_id,
    e.file_name,
    e.part_number,
    e.part_name,
    e.source_language_name,
    e.material AS drawing_material,
    b.material AS bom_material,
    COALESCE(e.material, b.material) AS reconciled_material,
    e.finish AS drawing_finish,
    b.finish AS bom_finish,
    COALESCE(e.finish, b.finish) AS reconciled_finish,
    e.missing_fields,
    CASE
        WHEN e.material IS NULL AND b.material IS NOT NULL THEN 'Filled from BOM'
        WHEN e.material IS NOT NULL THEN 'From drawing'
        ELSE 'MISSING'
    END AS material_source,
    CASE
        WHEN e.finish IS NULL AND b.finish IS NOT NULL THEN 'Filled from BOM'
        WHEN e.finish IS NOT NULL THEN 'From drawing'
        ELSE 'MISSING'
    END AS finish_source,
    e.critical_dimensions,
    e.bom AS drawing_bom,
    e.parsed
FROM DRAWING_EXTRACTIONS e
LEFT JOIN BOM_PARTS b ON e.part_number = b.part_number;
