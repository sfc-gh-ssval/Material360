-- =============================================================================
-- 01_stage_and_tables.sql — Drawing stage, extraction table, BOM master table
-- Idempotent: IF NOT EXISTS, so re-running never drops data.
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

-- Original drawing files (PDF / PNG / JPG / TIFF). Server-side encryption is
-- required for AI_COMPLETE + TO_FILE; directory table lets the backend refresh it.
CREATE STAGE IF NOT EXISTS DRAWING_STAGE
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    DIRECTORY = (ENABLE = TRUE);

-- One row per extracted drawing (written by EXTRACT_DRAWING).
CREATE TABLE IF NOT EXISTS DRAWING_EXTRACTIONS (
    EXTRACTION_ID        VARCHAR DEFAULT UUID_STRING(),
    FILE_NAME            VARCHAR NOT NULL,
    FILE_PATH            VARCHAR,
    EXTRACTION_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    MODEL_USED           VARCHAR DEFAULT 'claude-sonnet-4-6',
    DRAWING_TYPE         VARCHAR DEFAULT 'MECHANICAL',
    SOURCE_LANGUAGE      VARCHAR,              -- ISO 639-1 code, e.g. 'it'
    SOURCE_LANGUAGE_NAME VARCHAR,              -- e.g. 'Italian'
    WAS_TRANSLATED       BOOLEAN DEFAULT FALSE,
    PART_NUMBER          VARCHAR,
    PART_NAME            VARCHAR,              -- translated to English
    ORIGINAL_PART_NAME   VARCHAR,              -- as written on the drawing
    REVISION             VARCHAR,
    MATERIAL             VARCHAR,
    FINISH               VARCHAR,              -- translated to English
    ORIGINAL_FINISH      VARCHAR,
    COSMETIC_REQUIREMENT VARCHAR,
    WEIGHT_KG            NUMBER(10,2),
    BBOX_X               NUMBER(10,3),         -- overall envelope, mm
    BBOX_Y               NUMBER(10,3),
    BBOX_Z               NUMBER(10,3),
    BBOX_SOURCE          VARCHAR,              -- how the envelope was derived
    MISSING_FIELDS       VARIANT,              -- array of field names not found
    CRITICAL_DIMENSIONS  VARIANT,              -- [{value, tolerance, location_on_drawing, source_evidence}]
    BOM                  VARIANT,              -- translated BOM lines
    ORIGINAL_BOM         VARIANT,              -- BOM lines in source language
    RAW_RESPONSE         VARCHAR,              -- raw model output
    PARSED               VARIANT,              -- parsed JSON
    SEARCH_TEXT          VARCHAR,              -- denormalized text indexed by DRAWING_SEARCH
    DESIGNER             VARCHAR,
    DRAFTSMAN            VARCHAR,
    PRIMARY KEY (EXTRACTION_ID)                -- metadata only (not enforced)
);

-- BOM master data used to fill gaps in drawing extractions (joined on PART_NUMBER).
CREATE TABLE IF NOT EXISTS BOM_PARTS (
    BOM_ID          VARCHAR DEFAULT UUID_STRING(),
    PART_NUMBER     VARCHAR,
    PART_NAME       VARCHAR,
    MATERIAL        VARCHAR,
    FINISH          VARCHAR,
    QUANTITY        NUMBER(38,0),
    UNIT_COST       NUMBER(10,2),
    SUPPLIER        VARCHAR,
    SOURCE_DOCUMENT VARCHAR,
    PRIMARY KEY (BOM_ID)                       -- metadata only (not enforced)
);
