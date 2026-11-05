# Student Attendance System

A runnable Python command-line project for registering students, recording daily attendance, generating reports, calculating individual attendance percentages, and exporting records to CSV. Data is stored locally in SQLite.

## Real-life problem
Schools and colleges need accurate attendance records. Paper registers can be time-consuming to maintain, difficult to search, and prone to calculation errors. This system digitizes basic attendance management and makes records easier to review.

## Features
- Register students with a unique student ID, name, and class.
- Record attendance as **Present**, **Absent**, or **Late**.
- Prevent duplicate attendance entries for the same student on the same date.
- View attendance reports, optionally filtered by date or class.
- Calculate an individual student's attendance percentage.
- Export attendance records to CSV.
- Local SQLite storage; no third-party dependencies.

## Requirements
- Python 3.9 or newer
- No external packages required

## Run the project
Open a terminal in the project root.

Register a student:
```bash
python -m attendance_system.app add-student --id S001 --name "Aarav Shah" --class FY-BSc
```

Mark attendance:
```bash
python -m attendance_system.app mark --id S001 --status Present --date 2026-11-05
```

List students:
```bash
python -m attendance_system.app students
```

View a date-wise report:
```bash
python -m attendance_system.app report --date 2026-11-05
```

View a student's summary:
```bash
python -m attendance_system.app summary --id S001
```

Export records:
```bash
python -m attendance_system.app export --output exports/attendance.csv
```

Use a custom database by placing `--db path/to/file.db` before the subcommand.

## Run automated tests
```bash
python -m unittest discover -s tests -v
```

## Project structure
```text
student_attendance_system/
├── attendance_system/
│   ├── __init__.py
│   └── app.py
├── tests/
│   └── test_app.py
├── data/
│   └── .gitkeep
├── docs/
│   └── project_report.pdf
├── README.md
├── requirements.txt
└── .gitignore
```

## Database design
- `students`: student_id (primary key), name, class_name, created_at
- `attendance`: id (primary key), student_id (foreign key), attendance_date, status, remarks, created_at
- A unique constraint on `(student_id, attendance_date)` prevents duplicate daily records.

## Privacy
The SQLite database is created locally at `data/attendance.db`. Database files are excluded from Git so student records are not accidentally published.

## Future enhancements
A graphical interface, role-based login for faculty, bulk attendance marking, timetable integration, downloadable PDF attendance sheets, and class-wise analytics could be added in later versions.
