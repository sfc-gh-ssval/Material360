-- =============================================================================
-- 00_setup.sql — Database, schema and (optional) warehouse for Material360
-- Requires a role that can create databases/schemas and use Cortex AI
-- (SNOWFLAKE.CORTEX_USER database role).
-- =============================================================================
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS;

-- Optional: dedicated warehouse. Skip if you already have one and set
-- SNOWFLAKE_WAREHOUSE in .env (and the WAREHOUSE in 04_search_service.sql).
CREATE WAREHOUSE IF NOT EXISTS MATERIAL360_WH
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;
