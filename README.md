# Inventory Automation & Validation System

A small, production-style Python inventory system demonstrating:
- SQLite-backed persistence with audit trail
- CSV batch import validation and file organization
- Validation utilities and QA test suite
- Auto-updated inventory charts and logging

Status: demo / production-style. CI uses Python 3.12.

---

## Quick start

Prerequisites
- Python 3.12
- pip

Setup
```bash
git clone https://github.com/SinaKarimi95/internal-process-automation-mock.git
cd internal-process-automation-mock
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Workflow (recommended)

This project separates CSV import/validation from the interactive app. Recommended order:

1. Validate & import CSV files (processes files in `imports/`)
2. Run the interactive inventory app (`inventory_system.py`)

Validate/import CSVs
```bash
# Place .csv files in the imports/ directory, then:
python3 validate_imports.py
```
What this does:
- Validates each CSV (structure + business rules).
- Imports valid rows into the SQLite database.
- Moves processed files to `imports/processed/` and invalid files to `imports/failed/`.
- If imports succeed, the app chart update callback (`system.update_chart`) is called to regenerate the chart.

Run the interactive app
```bash
python3 inventory_system.py
```
Typical interactive menu (example):
- 1 — Display inventory (regenerates chart)
- 2 — Add / remove stock (guided prompts)
- 3 — Exit

Note: `inventory_system.py` does NOT automatically process the `imports/` directory on startup. Run `validate_imports.py` first if you want new CSVs imported before starting the app.

One-line run (validate then app)
```bash
python3 validate_imports.py && python3 inventory_system.py
```

---

## CSV format

Required header and columns:
- item_id (integer)
- item_name (string)
- quantity (integer, non-negative)
- location (string)

Example CSV:
```csv
item_id,item_name,quantity,location
101,Widget A,150,Warehouse 1
102,Widget B,50,Warehouse 2
```

Files must be named with a `.csv` extension and placed directly inside `imports/`.

---

## Seed data (sample_data/)

The `sample_data/` directory contains a small, deterministic CSV used as a seed for local runs and for the test suites.

Purpose
- Provides a predictable dataset so `inventory_system.py`, `validate_imports.py`, and the tests (`test_refactor.py` and `test_qa.py`) behave the same on every machine.
- Makes it easy to run the app and CI without requiring external input.

Notes
- The canonical runtime data store is the SQLite database managed by the repository. CSVs dropped into `imports/` are validated and imported into the DB; the importer moves processed files to `imports/processed/`.
- `sample_data/inventory.csv` is only a seed (sample) and is not updated by the import workflow. Keep it small and free of any sensitive or personal information.
- If you prefer tests to validate the DB state instead of the seed file, consider updating tests to create and use a temporary DB or to instantiate `InventorySystem` with a dynamically generated seed file (recommended for more production-like testing).

Example (how tests use it)
- By default tests initialize the system with the seed:
```python
system = InventorySystem("sample_data/inventory.csv")
```

---

## Logs, imports and automatic directory creation

- When you run `python3 inventory_system.py`, the application will automatically create the following directories if they don't exist:
  - `logs/`  — where `logs/inventory_system.log` is written via a RotatingFileHandler
  - `screenshots/` — where generated charts (e.g. `inventory_levels.png`) are saved

- When you run `python3 validate_imports.py` (it instantiates `InventoryImporter`), the importer will automatically create:
  - `imports/`
  - `imports/processed/`
  - `imports/failed/`
  These directories are created using `os.makedirs(..., exist_ok=True)` before processing.

- Because log files often contain runtime/personal info, it's common to keep `logs/` out of version control (check `.gitignore`). Recreating these directories locally is safe — the app/importer will regenerate them as needed.

---

## Testing & QA

Run architecture/import checks:
```bash
python3 test_refactor.py
```

Run validation and audit QA:
```bash
python3 test_qa.py
```

These scripts exercise validators, audit queries, and repository/api surface used in CI.

---

## Project layout (important files)

- inventory_system.py        — Interactive application (main entrypoint)
- repository.py              — Data access layer (InventoryRepository)
- database.py                — SQLite management and schema
- importer.py                — InventoryImporter (CSV validation & import)
- validate_imports.py        — CLI wrapper that runs imports over `imports/`
- validators.py              — Validation utilities (used by importer/tests)
- audit_queries.py           — Read-only audit/query helpers
- test_refactor.py           — Architecture/deployment checks (CI)
- test_qa.py                 — QA tests for validation & audit logic
- imports/                   — Drop CSVs here (processed/failed subfolders)
- sample_data/               — Seed/sample CSV files
- screenshots/               — Chart images
- logs/                      — Application logs
- LICENSE                    — MIT license (existing in this repo)

---

## Troubleshooting

- CSVs not processed? Ensure files are in `imports/` (not nested) and have a `.csv` extension.
- Import failed? Inspect `imports/failed/` and `logs/inventory_system.log` for validation errors.
- App runs but data not updated? Confirm you ran `validate_imports.py` before starting the app (imports update the DB; the app reads the DB).
- Tests failing? Use the same Python version as CI (3.12) and an isolated venv.

---


## License & contact

This repository is licensed under the MIT License. See the `LICENSE` file for details.