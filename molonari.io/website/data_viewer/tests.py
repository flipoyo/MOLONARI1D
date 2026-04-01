import sqlite3
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse

from .views import _query_molonaviz_db


class DataViewerViewTests(TestCase):
    """Tests for the sensor data page."""

    def test_no_db_configured(self):
        """When MOLONAVIZ_DB_PATH is empty, display an info message."""
        with self.settings(MOLONAVIZ_DB_PATH=""):
            response = self.client.get(reverse("data_viewer:sensor_data"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MOLONAVIZ_DB_PATH")

    def test_db_file_not_found(self):
        """When the path does not exist, display an error."""
        with self.settings(MOLONAVIZ_DB_PATH="/nonexistent/db.sqlite3"):
            response = self.client.get(reverse("data_viewer:sensor_data"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not found")


class QueryMolonavizDBTests(TestCase):
    """Unit tests for the low-level DB query helper."""

    def test_missing_file(self):
        result, error = _query_molonaviz_db("/does/not/exist.db")
        self.assertIsNone(result)
        self.assertIn("not found", error)

    def test_valid_database(self):
        """Create a temporary SQLite DB and verify we can read it."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            db_path = tmp.name

        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE RawMeasuresTemp (Date TEXT, Temp1 REAL, Temp2 REAL)"
        )
        conn.execute(
            "INSERT INTO RawMeasuresTemp VALUES ('2025-01-01 12:00:00', 10.5, 11.2)"
        )
        conn.commit()
        conn.close()

        result, error = _query_molonaviz_db(db_path)
        self.assertIsNone(error)
        headers, rows = result
        self.assertEqual(headers, ["Date", "Temp1", "Temp2"])
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["Temp1"], 10.5)

        Path(db_path).unlink()

    def test_missing_table(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            db_path = tmp.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE OtherTable (id INTEGER)")
        conn.commit()
        conn.close()

        result, error = _query_molonaviz_db(db_path, table_name="RawMeasuresTemp")
        self.assertIsNone(result)
        self.assertIn("not found", error)

        Path(db_path).unlink()

    def test_invalid_table_name_rejected(self):
        """Table names with SQL injection characters must be rejected."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tmp:
            db_path = tmp.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE safe_table (id INTEGER)")
        conn.commit()
        conn.close()

        result, error = _query_molonaviz_db(db_path, table_name="t; DROP TABLE x")
        self.assertIsNone(result)
        self.assertIn("Invalid", error)

        Path(db_path).unlink()
