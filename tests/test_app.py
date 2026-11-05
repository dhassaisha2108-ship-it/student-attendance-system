import tempfile
import unittest
from pathlib import Path
from attendance_system.app import (
    add_student, list_students, mark_attendance, attendance_report,
    student_summary, export_csv
)

class AttendanceSystemTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        add_student("S001", "Aarav Shah", "FY-BSc", self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_student_registration_and_listing(self):
        self.assertEqual(len(list_students(self.db)), 1)

    def test_mark_and_report_attendance(self):
        mark_attendance("S001", "Present", "2026-11-05", db_path=self.db)
        rows = attendance_report("2026-11-05", db_path=self.db)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "Present")

    def test_duplicate_attendance_is_rejected(self):
        mark_attendance("S001", "Present", "2026-11-05", db_path=self.db)
        with self.assertRaises(ValueError):
            mark_attendance("S001", "Absent", "2026-11-05", db_path=self.db)

    def test_student_summary_percentage(self):
        mark_attendance("S001", "Present", "2026-11-03", db_path=self.db)
        mark_attendance("S001", "Absent", "2026-11-04", db_path=self.db)
        result = student_summary("S001", self.db)
        self.assertEqual(result[1:5], (2, 1, 1, 0))
        self.assertEqual(result[5], 50.0)

    def test_csv_export(self):
        mark_attendance("S001", "Late", "2026-11-05", db_path=self.db)
        output = Path(self.tmp.name) / "attendance.csv"
        self.assertEqual(export_csv(output, db_path=self.db), 1)
        self.assertIn("Aarav Shah", output.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
