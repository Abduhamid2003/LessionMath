from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _column_names(engine: Engine, table: str) -> set[str]:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns(table)}


def run_light_migrations(engine: Engine) -> None:
    """Add new columns to existing SQLite/Postgres DBs without Alembic."""
    patches = {
        "lessons": [
            ("title_en", "VARCHAR(300) DEFAULT ''"),
            ("content_en", "TEXT DEFAULT ''"),
            ("is_published", "BOOLEAN DEFAULT 1"),
            ("image_urls", "TEXT DEFAULT '[]'"),
        ],
        "tests": [
            ("title_en", "VARCHAR(300) DEFAULT ''"),
            ("description_en", "TEXT DEFAULT ''"),
            ("author_id", "INTEGER"),
            ("is_published", "BOOLEAN DEFAULT 1"),
            ("class_id", "INTEGER"),
        ],
        "test_questions": [
            ("question_en", "TEXT DEFAULT ''"),
            ("options_en", "TEXT DEFAULT '[]'"),
            ("hint_en", "TEXT DEFAULT ''"),
        ],
        "achievements": [
            ("title_en", "VARCHAR(200) DEFAULT ''"),
            ("description_en", "TEXT DEFAULT ''"),
        ],
    }
    with engine.begin() as conn:
        for table, cols in patches.items():
            existing = _column_names(engine, table)
            for col_name, col_def in cols:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
