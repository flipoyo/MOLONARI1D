import re
import sqlite3
from pathlib import Path

from django.conf import settings
from django.shortcuts import render

# Only allow simple identifiers as table names to prevent SQL injection.
_SAFE_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _query_molonaviz_db(db_path, table_name="RawMeasuresTemp", limit=128):
    """Read sensor data from the Molonaviz SQLite database.

    Returns a tuple of (headers, rows) or raises an error message string.
    """
    if not Path(db_path).is_file():
        return None, "Database file not found."

    if not _SAFE_TABLE_RE.match(table_name):
        return None, "Invalid table name."

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")  # noqa: S608
        headers = [row["name"] for row in cursor.fetchall()]
        if not headers:
            return None, f"Table '{table_name}' not found."

        cursor = conn.execute(
            f"SELECT * FROM {table_name} ORDER BY Date DESC LIMIT ?",  # noqa: S608
            (limit,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        return (headers, rows), None
    finally:
        conn.close()


def sensor_data(request):
    db_path = settings.MOLONAVIZ_DB_PATH
    context = {"headers": [], "rows": [], "error": None, "db_configured": bool(db_path)}

    if db_path:
        result, error = _query_molonaviz_db(db_path)
        if error:
            context["error"] = error
        else:
            context["headers"] = result[0]
            context["rows"] = result[1]

    return render(request, "data_viewer/sensor_data.html", context)
