# Inventory Automation & Validation System

## Why This Project Exists

**Portfolio project demonstrating validation-first architecture and QA practices.** Showcases input validation, audit trails, deterministic testing, error handling, and compliance ready, logging core competencies for QA, test automation, and validation engineering roles.

**What it does:**
- CRUD operations with comprehensive audit trail
- CSV batch import validation and automated processing
- Rotating logs with structured error handling
- Auto-updated inventory visualizations
- Transaction history and data consistency validation

![Inventory Levels](screenshots/inventory_levels.png)

## Quick Start

Prerequisites: Python 3.12, pip

```bash
git clone https://github.com/SinaKarimi95/internal-process-automation-mock.git
cd internal-process-automation-mock
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage Workflow

Recommended order: validate/import CSVs first, then run interactive app.

### 1. Validate & Import CSVs
```bash
python3 validate_imports.py
```
Validates each CSV against business rules, imports valid rows to SQLite database, and organizes processed files: `imports/processed/` (success) or `imports/failed/` (with errors).

### 2. Run Interactive App
```bash
python3 inventory_system.py
```
Interactive menu: Display inventory (with chart), Add/remove stock, or Exit.

### One-line Workflow
```bash
python3 validate_imports.py && python3 inventory_system.py
```

## CSV Format Requirements

Required columns: `item_id` (integer), `item_name` (string), `quantity` (non-negative integer), `location` (string).

```csv
item_id,item_name,quantity,location
101,Widget A,150,Warehouse 1
102,Widget B,50,Warehouse 2
```

Place `.csv` files in `imports/` directory (not nested subdirectories).

## Setup Notes

- **Seed Data**: `sample_data/inventory.csv` provides initial data for tests and app initialization. SQLite database is the canonical runtime store.
- **Auto-created Directories**: `logs/`, `screenshots/`, and `imports/` generated on first run as needed. Runtime directories excluded from version control.

## Testing & Validation

### Architecture & Structure Tests
```bash
python3 test_refactor.py
```
Validates code structure, imports, and deployment readiness.

### QA & Functional Tests
```bash
python3 test_qa.py
```
Tests validation functions, audit queries, and business logic.

## Validation Architecture

### Input Validation Layer
All user inputs validated before processing: type checking, range validation, business rule enforcement, with specific error messages for diagnostics.

### CSV Import Pipeline
Structure validation (columns, types) → Business logic validation (positive quantities, unique IDs) → Atomic processing with rollback → File preservation with error details.

### Database Consistency
Referential integrity checks, audit trail validation, transaction history verification.

## Key Project Files

- `inventory_system.py` — Interactive application (main entrypoint)
- `repository.py` — Data access layer with caching
- `database.py` — SQLite management and schema
- `importer.py` — CSV validation & import pipeline
- `validate_imports.py` — CLI wrapper for import processing
- `validators.py` — Pure validation functions
- `audit_queries.py` — Read-only audit/query helpers
- `test_refactor.py` — Architecture/deployment checks
- `test_qa.py` — QA tests for validation logic

## Troubleshooting

- **CSVs not imported?** Verify files in `imports/` with `.csv` extension
- **Import failed?** Check `imports/failed/` directory and `logs/inventory_system.log`
- **Data changes not reflected?** Run `validate_imports.py` before launching app
- **Tests failing?** Ensure Python 3.12 in isolated virtual environment

## Design Principles

- **Validation-First**: All inputs validated before use
- **Audit-Ready**: Every operation creates traceable records
- **Testable Architecture**: Pure functions, dependency injection patterns
- **Error Resilience**: Graceful handling of missing/invalid data
- **Deterministic Behavior**: Predictable test results across environments

## Dependencies

- **pandas==2.0.3** — Data manipulation and CSV processing
- **matplotlib==3.7.2** — Chart generation
- **sqlite3** — Database (built-in standard library)

## Exit Codes

`validate_imports.py` returns:
- `0` — Success or no files to process
- `1` — Import validation failures
- `2` — System error

## License

MIT License — see `LICENSE` file for details.