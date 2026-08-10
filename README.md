# Tunisie Telecom — File Processing Tool (Web MVP)

A Flask + pandas web app implementing the file-processing internship brief:
upload csv/txt/excel files, sort them, find & remove duplicates, compare or
merge two files, and export results in CSV/TXT/Excel/PDF.

This is a **working MVP skeleton**, not the full feature set — it covers the
"Must" priority items from the backlog (Epics 1, 2, 3, 9, 10, 11) so you have
a running app to build on. The remaining epics (sequence detection, file
splitting, template-based reformatting, column operations, column
reorder/add/remove/extract) already have their core logic written in
`app/services/operations.py` — they just need routes + templates wired up,
following the same pattern as `sort` and `duplicates`.

## Project structure

```
tt_file_processor/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes/
│   │   ├── main.py              # Home page
│   │   ├── single_file.py       # Epics 1-9 (upload, sort, duplicates, export)
│   │   └── multi_file.py        # Epics 10-11 (compare, merge)
│   ├── services/
│   │   ├── file_loader.py       # Unified csv/txt/xls/xlsx loader (Epic 1)
│   │   ├── operations.py        # All data operations, one function per epic
│   │   └── exporters.py         # Unified export engine (Epic 9)
│   ├── templates/               # Jinja2 + Bootstrap 5 templates
│   └── static/css/style.css
├── instance/
│   ├── uploads/                 # Uploaded files land here (gitignored)
│   └── outputs/                 # Generated result files (gitignored)
├── tests/
│   └── test_operations.py       # Unit tests for core logic (pytest)
├── requirements.txt
├── run.py                       # Entry point: python run.py
└── README.md
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open http://127.0.0.1:5000

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

## How the pieces fit together

- **`file_loader.py`** turns any uploaded csv/txt/xls/xlsx into a pandas
  DataFrame, detecting delimiter for text files automatically.
- **`operations.py`** is pure logic — no Flask, no HTTP — so every function
  can be unit-tested directly (see `tests/test_operations.py`). This is where
  you should add logic for the remaining epics (sequence detection, splitting,
  templating, column math, column reorder/add/remove/extract).
- **`exporters.py`** is the single place that knows how to write
  csv/txt/xlsx/pdf — every route reuses `exporters.export(df, path, fmt)`
  rather than reimplementing export logic per feature.
- **Routes** (`single_file.py`, `multi_file.py`) are intentionally thin: load
  data → call an `operations` function → call `exporters.export` → render/
  send the result. Session variables track "current file" / "last result" so
  a user can chain operations without re-uploading.

## Next steps (matches the backlog)

1. Wire up routes/templates for: sequence detection (Epic 4), file splitting
   (Epic 5), template-based reformatting (Epic 6), column string/math ops
   (Epic 7), column reorder/add/remove/extract (Epic 8) — logic already
   exists in `operations.py`.
2. Replace the temp-file session approach with a proper job/result store if
   you need multi-user concurrency.
3. Add drag-and-drop column reordering (HTMX + a small JS sortable list) for
   Epic 8.
4. Deploy behind gunicorn + nginx on the Tunisie Telecom intranet server
   (confirm with your supervisor whether one is available).
