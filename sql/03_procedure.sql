-- =============================================================================
-- 03_procedure.sql — EXTRACT_DRAWING(file_name)
-- One AI_COMPLETE vision call per drawing (claude-sonnet-4-6 + TO_FILE):
-- detects language, translates to English (originals kept), extracts title block,
-- critical dimensions / GD&T, bounding box, missing fields and BOM as JSON,
-- then parses it and inserts a row into DRAWING_EXTRACTIONS.
-- Usage:  CALL EXTRACT_DRAWING('EN_bracket_assy.pdf');
-- =============================================================================
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA ENGINEERING_DRAWINGS;

CREATE OR REPLACE PROCEDURE EXTRACT_DRAWING(FILE_NAME VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    raw_result VARCHAR;
    parsed_json VARIANT;
    v_part_number VARCHAR;
    v_part_name VARCHAR;
    v_original_part_name VARCHAR;
    v_revision VARCHAR;
    v_material VARCHAR;
    v_finish VARCHAR;
    v_original_finish VARCHAR;
    v_cosmetic VARCHAR;
    v_designer VARCHAR;
    v_draftsman VARCHAR;
    v_weight NUMBER(10,2);
    v_source_lang VARCHAR;
    v_source_lang_name VARCHAR;
    v_was_translated BOOLEAN;
    v_bbox_x NUMBER(10,3);
    v_bbox_y NUMBER(10,3);
    v_bbox_z NUMBER(10,3);
    v_bbox_source VARCHAR;
    v_search_text VARCHAR;
    v_missing_fields VARCHAR;
    v_critical_dims VARCHAR;
    v_bom VARCHAR;
    v_original_bom VARCHAR;
    extraction_prompt VARCHAR DEFAULT 'You are extracting structured data from a mechanical engineering drawing.
The drawing may be in ANY language (English, Italian, German, French, Spanish, etc.).

CRITICAL RULES:
1. DETECT the language of the title block and notes.
2. TRANSLATE all extracted values to English. Return originals in separate fields.
3. Only report a field value if it is ACTUALLY VISIBLE on the drawing. Do NOT guess.
4. If a field is not present, set it to null AND add its name to missing_fields.

Return ONLY a single JSON object (no markdown fences, no commentary) with this exact shape:

{
  "source_language": "<ISO 639-1 code>",
  "source_language_name": "<Full name>",
  "was_translated": true or false,
  "part_number": "string or null",
  "part_name": "translated to English or null",
  "original_part_name": "original language or null",
  "revision": "string or null",
  "material": "material grade as shown or null",
  "finish": "translated to English or null",
  "original_finish": "original language or null",
  "cosmetic_requirement": "translated to English or null",
  "designer": "name of designer/engineer from title block or null",
  "draftsman": "name of draftsman/drawn-by person from title block or null",
  "weight_kg": number or null,
  "critical_dimensions": [{"value": "dim with unit", "tolerance": "tol or null", "location_on_drawing": "translated to English", "source_evidence": "exact text from drawing"}],
  "bounding_box": {"x": number or null, "y": number or null, "z": number or null, "derived_from": "explanation"},
  "missing_fields": ["field names not found"],
  "bom": [{"pos": number, "description": "translated", "original_description": "original", "material": "mat", "qty": number}],
  "original_bom": [{"pos": number, "description": "original", "material": "mat", "qty": number}]
}

Rules:
- part_number, revision, material: copy exactly as shown (do not translate).
- part_name, finish, cosmetic_requirement, BOM descriptions, dimension locations: translate to English.
- designer, draftsman: copy the name exactly as shown in the title block. Look for fields like "Progettista", "Disegnatore", "Konstrukteur", "Gezeichnet", "Dessinateur", "Dessine par", "Disenado", "Dibujado" in non-English drawings.
- critical_dimensions: list EVERY dimensioned callout and GD&T annotation with source_evidence.
- bounding_box: only populate if overall envelope dims are stated. Explain in derived_from.
- If no BOM on drawing, return empty arrays.
- missing_fields: include any of part_number, part_name, revision, material, finish, cosmetic_requirement, bounding_box not found.
- Respond with JSON only.';
BEGIN
    SELECT AI_COMPLETE(
        'claude-sonnet-4-6',
        :extraction_prompt,
        TO_FILE('@SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS.DRAWING_STAGE', :file_name)
    ) INTO :raw_result;

    raw_result := REPLACE(REPLACE(:raw_result, '```json', ''), '```', '');
    parsed_json := TRY_PARSE_JSON(:raw_result);

    IF (parsed_json IS NULL) THEN
        RETURN OBJECT_CONSTRUCT('error', 'Failed to parse JSON', 'raw', :raw_result);
    END IF;

    v_part_number := parsed_json:part_number::VARCHAR;
    v_part_name := parsed_json:part_name::VARCHAR;
    v_original_part_name := parsed_json:original_part_name::VARCHAR;
    v_revision := parsed_json:revision::VARCHAR;
    v_material := parsed_json:material::VARCHAR;
    v_finish := parsed_json:finish::VARCHAR;
    v_original_finish := parsed_json:original_finish::VARCHAR;
    v_cosmetic := parsed_json:cosmetic_requirement::VARCHAR;
    v_designer := parsed_json:designer::VARCHAR;
    v_draftsman := parsed_json:draftsman::VARCHAR;
    v_weight := parsed_json:weight_kg::NUMBER(10,2);
    v_source_lang := parsed_json:source_language::VARCHAR;
    v_source_lang_name := parsed_json:source_language_name::VARCHAR;
    v_was_translated := parsed_json:was_translated::BOOLEAN;
    v_bbox_x := parsed_json:bounding_box:x::NUMBER(10,3);
    v_bbox_y := parsed_json:bounding_box:y::NUMBER(10,3);
    v_bbox_z := parsed_json:bounding_box:z::NUMBER(10,3);
    v_bbox_source := parsed_json:bounding_box:derived_from::VARCHAR;
    v_missing_fields := parsed_json:missing_fields::VARCHAR;
    v_critical_dims := parsed_json:critical_dimensions::VARCHAR;
    v_bom := parsed_json:bom::VARCHAR;
    v_original_bom := parsed_json:original_bom::VARCHAR;

    v_search_text := CONCAT_WS(' | ',
        'Part: ' || COALESCE(:v_part_number, ''),
        COALESCE(:v_part_name, ''),
        COALESCE(:v_original_part_name, ''),
        'Rev ' || COALESCE(:v_revision, ''),
        'Material: ' || COALESCE(:v_material, ''),
        'Finish: ' || COALESCE(:v_finish, ''),
        COALESCE(:v_original_finish, ''),
        'Weight: ' || COALESCE(:v_weight::VARCHAR, '') || ' kg',
        'Language: ' || COALESCE(:v_source_lang_name, ''),
        'Designer: ' || COALESCE(:v_designer, ''),
        'Draftsman: ' || COALESCE(:v_draftsman, '')
    );

    INSERT INTO DRAWING_EXTRACTIONS (
        file_name, file_path, model_used, drawing_type,
        source_language, source_language_name, was_translated,
        part_number, part_name, original_part_name, revision,
        material, finish, original_finish, cosmetic_requirement,
        designer, draftsman,
        weight_kg,
        bbox_x, bbox_y, bbox_z, bbox_source,
        missing_fields, critical_dimensions, bom, original_bom,
        raw_response, parsed, search_text
    )
    SELECT
        :file_name,
        '@SNOWFLAKE_INTELLIGENCE.ENGINEERING_DRAWINGS.DRAWING_STAGE/' || :file_name,
        'claude-sonnet-4-6', 'MECHANICAL',
        :v_source_lang, :v_source_lang_name, :v_was_translated,
        :v_part_number, :v_part_name, :v_original_part_name, :v_revision,
        :v_material, :v_finish, :v_original_finish, :v_cosmetic,
        :v_designer, :v_draftsman,
        :v_weight,
        :v_bbox_x, :v_bbox_y, :v_bbox_z, :v_bbox_source,
        TRY_PARSE_JSON(:v_missing_fields),
        TRY_PARSE_JSON(:v_critical_dims),
        TRY_PARSE_JSON(:v_bom),
        TRY_PARSE_JSON(:v_original_bom),
        :raw_result, :parsed_json, :v_search_text;

    RETURN parsed_json;
END;
$$;
