-- =============================================================================
-- 06_load_synthetic_drawings.sql — Upload and extract the sample drawings
-- Run from the repo root with Snowflake CLI (PUT needs a client, not Snowsight):
--   snow sql -c <connection> -f sql/06_load_synthetic_drawings.sql
-- Or upload via the app's Upload page instead.
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

PUT file://synthetic_drawings/*.pdf @DRAWING_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
ALTER STAGE DRAWING_STAGE REFRESH;

-- One AI_COMPLETE vision call each. Re-running inserts duplicate rows,
-- so only call for files you haven't extracted yet.
CALL EXTRACT_DRAWING('EN_bracket_assy.pdf');
CALL EXTRACT_DRAWING('EN_shaft_adapter.pdf');
CALL EXTRACT_DRAWING('EN_sensor_mount_degraded.pdf');
CALL EXTRACT_DRAWING('DE_kabelrinne_platte.pdf');
CALL EXTRACT_DRAWING('FR_gousset.pdf');
CALL EXTRACT_DRAWING('IT_telaio_saldato.pdf');
CALL EXTRACT_DRAWING('ES_placa_cubierta.pdf');
