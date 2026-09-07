# Tunisie Telecom File Processor

TT File Processor is a Python application for cleaning, transforming,
comparing, merging, and exporting structured files. It provides a browser-based
dashboard and can also run as a Windows desktop application through pywebview.

The web interface is served by Flask and exposed through a FastAPI/ASGI
wrapper. Data processing is performed with pandas, and the application keeps
uploaded files and generated results in the local `instance/` directory.

## Features

### File input

- CSV, TXT, XLS, XLSX, and PDF files containing tables or delimited text
- Automatic delimiter detection for comma, semicolon, tab, and pipe-separated text files
- File preview with row count, column count, and column names

### Single-file processing

- Sort by a selected column or by the complete row
- Find and remove duplicate rows, using all columns or selected columns
- Detect consecutive numeric sequences
- Split files by output-file count or rows per file
- Download split results as a ZIP archive
- Apply reusable templates to column values
- Add text, remove text, or apply arithmetic operations to column values
- Reorder, add, remove, and extract columns

### Two-file processing

- Compare complete rows or selected columns
- View matching rows and rows unique to either file
- Merge selected columns side by side by row position
- Export comparison and merge results

### Export and interface

- Export results as CSV, TXT, XLSX, or PDF
- Custom separators for CSV and TXT exports
- English and French interface options
- Responsive Flask/Jinja2 dashboard with Bootstrap-based templates

## Project structure

```
tt_file_processor/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes/
│   │   ├── main.py              # Dashboard and language selection
│   │   ├── single_file.py       # Single-file workflows
│   │   └── multi_file.py        # Compare and merge workflows
│   ├── services/
│   │   ├── file_loader.py       # Unified csv/txt/xls/xlsx loader (Epic 1)
│   │   ├── operations.py        # All data operations, one function per epic
│   │   └── exporters.py         # Unified export engine (Epic 9)
│   ├── templates/               # Jinja2 templates
│   └── static/css/style.css
├── instance/
│   ├── uploads/                 # Uploaded files land here (gitignored)
│   └── outputs/                 # Generated result files (gitignored)
├── tests/
│   └── test_operations.py       # Unit tests for processing logic
├── requirements.txt
├── run.py                       # Entry point: python run.py
├── TTFileProcessor.spec         # PyInstaller packaging configuration
└── README.md
```

## Installation

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the application

### Desktop mode

Run the following command to start the local server and open the application
in a native desktop window:

```bash
python run.py
```

### Browser mode

The application is available at `http://127.0.0.1:5000`. If the pywebview
window is unavailable in your environment, start the ASGI app with uvicorn:

```bash
uvicorn run:app --host 127.0.0.1 --port 5000
```

Then open `http://127.0.0.1:5000` in a browser.

## Running tests

```bash
python -m pytest tests/ -v
```

## Architecture

- `app/__init__.py` creates the Flask application, configures storage folders,
  registers routes, and mounts Flask inside FastAPI.
- `app/services/file_loader.py` converts supported uploads into pandas
  DataFrames and detects delimiters for text files.
- `app/services/operations.py` contains the processing logic independently of
  HTTP, which keeps it straightforward to test.
- `app/services/exporters.py` centralizes CSV, TXT, XLSX, and PDF output.
- `app/routes/` handles uploads, workflow pages, session state, and downloads.
- `run.py` starts uvicorn in a background thread and opens the local URL with
  pywebview.

## Storage and configuration

Uploaded files are stored in `instance/uploads/` and generated files are stored
in `instance/outputs/`. These directories are created automatically and are
ignored by Git. The application currently has no upload-size limit, so the
available disk space and memory of the machine determine practical file sizes.

For production use, replace the development `SECRET_KEY` in
`app/__init__.py` with a secret supplied through your deployment configuration.

## Windows executable

The repository includes `TTFileProcessor.spec` for PyInstaller packaging. A
local build can be created with:

```bash
pyinstaller TTFileProcessor.spec
```

The generated executable is placed in `dist/`.

## Dependencies

Runtime and test dependencies are listed in `requirements.txt`. The main
components are Flask, FastAPI, uvicorn, pandas, openpyxl, xlrd, pdfplumber,
ReportLab, pywebview, and PyInstaller.


