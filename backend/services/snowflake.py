import logging
from snowflake.snowpark import Session
from backend.config import settings

logger = logging.getLogger(__name__)

_session = None


def _create_session() -> Session:
    logger.info("Creating Snowflake session (browser auth may open)...")
    session = Session.builder.config("connection_name", settings.snowflake_connection_name).configs({
        "database": settings.snowflake_database,
        "schema": settings.snowflake_schema,
        "warehouse": settings.snowflake_warehouse,
    }).create()
    logger.info("Snowflake session established.")
    return session


def _is_alive(session: Session) -> bool:
    try:
        session.sql("SELECT 1").collect()
        return True
    except Exception:
        return False


def get_session() -> Session:
    global _session
    if _session is None or not _is_alive(_session):
        _session = _create_session()
    return _session


def init_session():
    """Call at startup to authenticate eagerly."""
    get_session()


def execute_query(sql: str, params: tuple = None) -> list[dict]:
    session = get_session()
    if params:
        for p in params:
            escaped = str(p).replace("'", "''") if isinstance(p, str) else str(p)
            sql = sql.replace("%s", f"'{escaped}'" if isinstance(p, str) else str(p), 1)
    try:
        rows = session.sql(sql).collect()
    except Exception:
        session = get_session()
        rows = session.sql(sql).collect()
    if not rows:
        return []
    return [row.as_dict() for row in rows]


def execute_scalar(sql: str, params: tuple = None):
    results = execute_query(sql, params)
    if results:
        first = results[0]
        keys = list(first.keys())
        return first[keys[0]] if keys else None
    return None
