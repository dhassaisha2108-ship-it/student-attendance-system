"""Student Attendance System: CLI attendance manager backed by SQLite."""
import argparse
import csv
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_DB = Path("data/attendance.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
    remarks TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    UNIQUE(student_id, attendance_date)
);
"""

def connect(db_path=DEFAULT_DB):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn

def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format.") from exc
    return value

def add_student(student_id, name, class_name, db_path=DEFAULT_DB):
    student_id, name, class_name = student_id.strip(), name.strip(), class_name.strip()
    if not student_id or not name or not class_name:
        raise ValueError("Student ID, name, and class are required.")
    with connect(db_path) as conn:
        try:
            conn.execute(
                "INSERT INTO students(student_id, name, class_name, created_at) VALUES (?, ?, ?, ?)",
                (student_id, name, class_name, datetime.now().isoformat(timespec="seconds"))
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Student ID '{student_id}' already exists.") from exc

def list_students(db_path=DEFAULT_DB):
    with connect(db_path) as conn:
        return conn.execute(
            "SELECT student_id, name, class_name FROM students ORDER BY class_name, name"
        ).fetchall()

def mark_attendance(student_id, status, attendance_date=None, remarks="", db_path=DEFAULT_DB):
    student_id = student_id.strip()
    status = status.title()
    attendance_date = validate_date(attendance_date or date.today().isoformat())
    if status not in {"Present", "Absent", "Late"}:
        raise ValueError("Status must be Present, Absent, or Late.")
    with connect(db_path) as conn:
        if not conn.execute("SELECT 1 FROM students WHERE student_id=?", (student_id,)).fetchone():
            raise ValueError(f"Student ID '{student_id}' was not found. Add the student first.")
        try:
            conn.execute(
                """INSERT INTO attendance(student_id, attendance_date, status, remarks, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, attendance_date, status, remarks.strip(),
                 datetime.now().isoformat(timespec="seconds"))
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Attendance for {student_id} on {attendance_date} is already recorded.") from exc

def attendance_report(attendance_date=None, class_name=None, db_path=DEFAULT_DB):
    attendance_date = validate_date(attendance_date) if attendance_date else None
    query = """SELECT s.student_id, s.name, s.class_name, a.attendance_date,
                      a.status, a.remarks
               FROM attendance a JOIN students s ON s.student_id=a.student_id"""
    clauses, params = [], []
    if attendance_date:
        clauses.append("a.attendance_date=?")
        params.append(attendance_date)
    if class_name:
        clauses.append("s.class_name=?")
        params.append(class_name)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY a.attendance_date DESC, s.class_name, s.name"
    with connect(db_path) as conn:
        return conn.execute(query, params).fetchall()

def student_summary(student_id, db_path=DEFAULT_DB):
    with connect(db_path) as conn:
        student = conn.execute(
            "SELECT student_id, name, class_name FROM students WHERE student_id=?", (student_id,)
        ).fetchone()
        if not student:
            raise ValueError(f"Student ID '{student_id}' was not found.")
        counts = conn.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present,
                      SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) AS absent,
                      SUM(CASE WHEN status='Late' THEN 1 ELSE 0 END) AS late
               FROM attendance WHERE student_id=?""", (student_id,)
        ).fetchone()
    total = counts["total"]
    present = counts["present"] or 0
    return student, total, present, counts["absent"] or 0, counts["late"] or 0, (
        round(present * 100 / total, 2) if total else 0.0
    )

def export_csv(output, attendance_date=None, class_name=None, db_path=DEFAULT_DB):
    rows = attendance_report(attendance_date, class_name, db_path)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "name", "class", "date", "status", "remarks"])
        writer.writerows([tuple(row) for row in rows])
    return len(rows)

def build_parser():
    parser = argparse.ArgumentParser(description="Manage student attendance locally.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database file")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add-student", help="Register a student")
    add.add_argument("--id", required=True, dest="student_id")
    add.add_argument("--name", required=True)
    add.add_argument("--class", required=True, dest="class_name")
    listing = sub.add_parser("students", help="List registered students")
    mark = sub.add_parser("mark", help="Record attendance")
    mark.add_argument("--id", required=True, dest="student_id")
    mark.add_argument("--status", required=True, choices=["Present", "Absent", "Late"])
    mark.add_argument("--date", default=date.today().isoformat())
    mark.add_argument("--remarks", default="")
    report = sub.add_parser("report", help="View attendance records")
    report.add_argument("--date", help="Filter by YYYY-MM-DD")
    report.add_argument("--class", dest="class_name", help="Filter by class")
    summary = sub.add_parser("summary", help="View an individual student's attendance summary")
    summary.add_argument("--id", required=True, dest="student_id")
    export = sub.add_parser("export", help="Export attendance records to CSV")
    export.add_argument("--output", type=Path, default=Path("exports/attendance.csv"))
    export.add_argument("--date", help="Filter by YYYY-MM-DD")
    export.add_argument("--class", dest="class_name", help="Filter by class")
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "add-student":
            add_student(args.student_id, args.name, args.class_name, args.db)
            print(f"Student {args.student_id} registered.")
        elif args.command == "students":
            rows = list_students(args.db)
            print("No students registered." if not rows else
                  "\n".join(f"{r['student_id']} | {r['name']} | {r['class_name']}" for r in rows))
        elif args.command == "mark":
            mark_attendance(args.student_id, args.status, args.date, args.remarks, args.db)
            print(f"{args.status} attendance recorded for {args.student_id} on {args.date}.")
        elif args.command == "report":
            rows = attendance_report(args.date, args.class_name, args.db)
            if not rows:
                print("No attendance records found.")
            for r in rows:
                print(f"{r['attendance_date']} | {r['class_name']} | {r['student_id']} | "
                      f"{r['name']} | {r['status']} | {r['remarks']}")
        elif args.command == "summary":
            student, total, present, absent, late, percentage = student_summary(args.student_id, args.db)
            print(f"Attendance summary: {student['name']} ({student['student_id']})")
            print(f"Class: {student['class_name']} | Sessions: {total} | Present: {present} | "
                  f"Absent: {absent} | Late: {late} | Attendance: {percentage:.2f}%")
        elif args.command == "export":
            count = export_csv(args.output, args.date, args.class_name, args.db)
            print(f"Exported {count} record(s) to {args.output}.")
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
