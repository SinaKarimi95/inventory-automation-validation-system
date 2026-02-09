"""Validate and process all CSVs in `imports/`.

Usage:
    python3 validate_imports.py

Exit codes:
    0 - all processed files succeeded (or no files found)
    1 - import errors occurred (one or more files failed)
    2 - unexpected error
"""

import sys
from inventory_system import InventorySystem
from importer import InventoryImporter
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMPORTS_DIR = os.path.join(BASE_DIR, "imports")
PROCESSED_DIR = os.path.join(IMPORTS_DIR, "processed")
FAILED_DIR = os.path.join(IMPORTS_DIR, "failed")


def main():
    try:
        system = InventorySystem(os.path.join(BASE_DIR, "sample_data", "inventory.csv"))
        importer = InventoryImporter(
            repository=system.repository,
            imports_dir=IMPORTS_DIR,
            processed_dir=PROCESSED_DIR,
            failed_dir=FAILED_DIR,
            on_success_callback=system.update_chart,
        )

        results = importer.process_all_imports()

        # Print human-readable summary
        print("Import Summary:")
        print(f"  Processed: {results['processed']}")
        print(f"  Failed:    {results['failed']}")
        print(f"  Skipped:   {results['skipped']}")

        if results["details"]:
            print("\nDetails:")
            for d in results["details"]:
                status = d["status"].upper()
                print(f" - {d['filename']}: {status}")
                if d["errors"]:
                    for err in d["errors"]:
                        print(f"     » {err}")

        # Exit non-zero if any failed
        if results["failed"] > 0:
            print(
                "\nOne or more imports failed. See logs and the imports/failed/ directory."
            )
            return 1

        print("\nAll imports processed successfully.")
        return 0

    except Exception as e:
        print(f"Unexpected error while processing imports: {e}")
        return 2


if __name__ == "__main__":
    code = main()
    sys.exit(code)
