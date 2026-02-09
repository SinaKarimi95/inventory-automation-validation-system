# Inventory Automation & Validation System

A small, production-style inventory system demonstrating automation, validation, audit logging, and QA-oriented workflows.

SQLite-backed inventory tracker with:
- CRUD operations with audit trail
- CSV batch import validation and sorting
- Rotating logs
- Auto-updated bar charts


![Inventory Levels](screenshots/inventory_levels.png)

## Quick Start

```bash
git clone <repo-url>
cd internal-process-automation-mock
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 inventory_system.py
```

## Usage

Run the app:
- `1` — Display inventory (regenerates chart)
- `2` — Add/remove stock
- `3` — Exit

Drop CSVs into `imports/` and run:
```bash
python3 validate_imports.py
```

Valid files move to `imports/processed/`, invalid to `imports/failed/`.

## Logging

Logs go to `logs/inventory_system.log`. View with:

```bash
tail -f logs/inventory_system.log
```

---

## QA & Validation

```bash
python3 test_refactor.py    # code structure checks
python3 test_qa.py          # validation and audit logic
python3 validate_imports.py # process CSVs in imports/
```

## Design Notes

- SQLite used for simplicity and auditability (no external dependencies)
- CSV imports are validated before mutating state
- Failed imports are preserved for inspection instead of discarded
- Logging favors traceability over verbosity
