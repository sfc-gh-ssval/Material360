import json
from backend.services.snowflake import execute_query, execute_scalar
from backend.config import settings

EXTRACTION_PROMPT = """You are extracting structured data from a mechanical engineering drawing.
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
  "designer": "name of the designer/engineer as shown in title block or null",
  "draftsman": "name of the draftsman/drawn-by person as shown in title block or null",
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
- critical_dimensions: list EVERY dimensioned callout and GD&T annotation with source_evidence.
- bounding_box: only populate if overall envelope dims are stated. Explain in derived_from.
- If no BOM on drawing, return empty arrays.
- designer, draftsman: copy the name exactly as shown in the title block. These are the people who designed/drew it. Look for fields like "Progettista", "Disegnatore", "Konstrukteur", "Gezeichnet", "Dessinateur", "Dessiné par", "Diseñado", "Dibujado" in non-English drawings.
- missing_fields: include any of part_number, part_name, revision, material, finish, cosmetic_requirement, bounding_box not found.
- Respond with JSON only."""


def extract_drawing(file_name: str) -> dict:
    """Call the stored procedure to extract drawing data."""
    results = execute_query("CALL EXTRACT_DRAWING(%s)", (file_name,))
    if results:
        return results[0].get("EXTRACT_DRAWING", {})
    return {"error": "No result from extraction"}


def search_drawings(query: str, limit: int = 5) -> list[dict]:
    """Search drawings using Cortex Search."""
    search_query = json.dumps({
        "query": query,
        "columns": ["part_number", "part_name", "material", "finish", "file_name",
                     "revision", "source_language_name", "was_translated",
                     "missing_fields_text", "critical_dimensions_text", "bom_text",
                     "bbox_x", "bbox_y", "bbox_z", "weight_kg", "cosmetic_requirement",
                     "original_part_name", "original_finish"],
        "limit": limit,
    })
    fqn = f"{settings.snowflake_database}.{settings.snowflake_schema}.{settings.search_service}"
    sql = f"SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW('{fqn}', %s) AS results"
    result = execute_scalar(sql, (search_query,))
    if result:
        parsed = json.loads(result) if isinstance(result, str) else result
        return parsed.get("results", [])
    return []


def agent_chat(question: str) -> str:
    """Agent pattern: search drawings, then use AI_COMPLETE to answer."""
    # Step 1: Search for relevant drawings
    search_results = search_drawings(question, limit=5)

    # Step 2: Build context from search results
    context = "RELEVANT ENGINEERING DRAWINGS:\n\n"
    for i, r in enumerate(search_results, 1):
        context += f"--- Drawing {i} ---\n"
        context += f"Part Number: {r.get('part_number', 'N/A')}\n"
        context += f"Part Name: {r.get('part_name', 'N/A')}\n"
        context += f"File: {r.get('file_name', 'N/A')}\n"
        context += f"Material: {r.get('material', 'N/A')}\n"
        context += f"Finish: {r.get('finish', 'N/A')}\n"
        context += f"Revision: {r.get('revision', 'N/A')}\n"
        context += f"Language: {r.get('source_language_name', 'N/A')}\n"
        if r.get('original_part_name'):
            context += f"Original Name: {r.get('original_part_name')}\n"
        context += f"Missing Fields: {r.get('missing_fields_text', '[]')}\n"
        context += f"Dimensions: {r.get('critical_dimensions_text', 'N/A')}\n"
        context += f"BOM: {r.get('bom_text', 'N/A')}\n"
        context += f"Bounding Box: {r.get('bbox_x', '?')} x {r.get('bbox_y', '?')} x {r.get('bbox_z', '?')} mm\n"
        context += f"Weight: {r.get('weight_kg', 'N/A')} kg\n"
        context += f"Cosmetic: {r.get('cosmetic_requirement', 'N/A')}\n\n"

    prompt = f"""You are an engineering drawing analysis assistant. Answer the user's question using ONLY the drawing data provided below.

{context}

USER QUESTION: {question}

FORMATTING RULES:
- When listing multiple drawings or comparing data, ALWAYS use a markdown table.
- Use columns like: Part Number, Part Name, Material, Finish, Language, File, etc. as appropriate.
- After the table, add a brief summary sentence highlighting key findings.
- Always cite specific part numbers.
- If a drawing was translated, show the original language in the table.
- Be precise about measurements.
- If the data doesn't contain enough info to answer, say so.
- Use markdown formatting (bold, headers, tables) for readability."""

    sql = "SELECT AI_COMPLETE(%s, %s) AS answer"
    answer = execute_scalar(sql, (settings.model_name, prompt))
    if not answer:
        return "No answer generated."
    # AI_COMPLETE returns a JSON-encoded string — decode it properly
    answer = str(answer)
    try:
        import json
        decoded = json.loads(answer)
        if isinstance(decoded, str):
            answer = decoded
    except (json.JSONDecodeError, TypeError):
        # Fallback: manual unescaping
        if answer.startswith('"') and answer.endswith('"'):
            answer = answer[1:-1]
        answer = answer.replace('\\n', '\n').replace('\\"', '"')
    return answer
