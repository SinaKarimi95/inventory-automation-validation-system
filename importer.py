"""CSV Import Pipeline - Validation & Batch Processing

Handles automated CSV imports with validation and error handling.
Watches imports/ directory and processes files in batch with transaction logging.
"""

import os
import shutil
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("inventory_system")


class CSVValidator:
    """Validates CSV structure and content before import."""

    # Required columns for import
    REQUIRED_COLUMNS = {"item_id", "item_name", "quantity", "location"}

    # Expected data types
    EXPECTED_TYPES = {
        "item_id": "integer",
        "item_name": "string",
        "quantity": "integer",
        "location": "string",
    }

    @staticmethod
    def validate_file(csv_path):
        """
        Validate a CSV file structure and content.

        Args:
            csv_path (str): Path to CSV file

        Returns:
            tuple: (is_valid: bool, errors: list, dataframe: pd.DataFrame or None)
        """
        errors = []

        # Check file exists
        if not os.path.exists(csv_path):
            return False, [f"File not found: {csv_path}"], None

        # Try to read CSV
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            return False, [f"Failed to parse CSV: {str(e)}"], None

        # Check for empty file
        if len(df) == 0:
            return False, ["CSV file is empty"], None

        # Check required columns
        missing_cols = CSVValidator.REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")

        if errors:
            return False, errors, None

        # Validate data types and values
        type_errors = CSVValidator._validate_data_types(df)
        errors.extend(type_errors)

        # Validate business logic
        logic_errors = CSVValidator._validate_business_logic(df)
        errors.extend(logic_errors)

        if errors:
            return False, errors, None

        return True, [], df

    @staticmethod
    def _validate_data_types(df):
        """
        Validate column data types.

        Args:
            df (pd.DataFrame): CSV data

        Returns:
            list: List of validation errors (empty if valid)
        """
        errors = []

        # Check item_id is integer
        if not pd.api.types.is_integer_dtype(df["item_id"]):
            errors.append("Column 'item_id' must contain integers")

        # Check quantity is integer
        if not pd.api.types.is_integer_dtype(df["quantity"]):
            errors.append("Column 'quantity' must contain integers")

        # Check item_name is string
        if not pd.api.types.is_object_dtype(df["item_name"]):
            errors.append("Column 'item_name' must contain text")

        # Check location is string
        if not pd.api.types.is_object_dtype(df["location"]):
            errors.append("Column 'location' must contain text")

        return errors

    @staticmethod
    def _validate_business_logic(df):
        """
        Validate business logic constraints.

        Args:
            df (pd.DataFrame): CSV data

        Returns:
            list: List of validation errors (empty if valid)
        """
        errors = []

        # Check for negative quantities
        negative_qty = df[df["quantity"] < 0]
        if not negative_qty.empty:
            item_ids = negative_qty["item_id"].tolist()
            errors.append(f"Negative quantities not allowed. Items: {item_ids}")

        # Check for duplicate item_ids
        duplicates = df[df.duplicated(subset=["item_id"], keep=False)]
        if not duplicates.empty:
            dup_ids = duplicates["item_id"].unique().tolist()
            errors.append(f"Duplicate item IDs found: {dup_ids}")

        # Check for null values
        null_cols = df.columns[df.isnull().any()].tolist()
        if null_cols:
            errors.append(f"NULL values found in columns: {', '.join(null_cols)}")

        return errors


class InventoryImporter:
    """Processes CSV files with validation and file organization."""

    def __init__(
        self,
        repository,
        imports_dir,
        processed_dir,
        failed_dir,
        on_success_callback=None,
    ):
        """Initialize importer.

        Args:
            repository: InventoryRepository instance
            imports_dir (str): Directory to watch for import files
            processed_dir (str): Directory for successfully processed files
            failed_dir (str): Directory for failed imports
            on_success_callback (callable): Optional callback function called after successful import
        """
        self.repository = repository
        self.imports_dir = imports_dir
        self.processed_dir = processed_dir
        self.failed_dir = failed_dir
        self.on_success_callback = on_success_callback

        # Create directories if they don't exist
        os.makedirs(imports_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(failed_dir, exist_ok=True)

        logger.info(
            f"Importer initialized - imports_dir: {imports_dir}, "
            f"processed_dir: {processed_dir}, failed_dir: {failed_dir}"
        )

    def process_all_imports(self):
        """Process all CSV files in the imports directory.

        Returns:
            dict: Summary of import results
        """
        results = {"processed": 0, "failed": 0, "skipped": 0, "details": []}

        if not os.path.exists(self.imports_dir):
            logger.warning(f"Imports directory does not exist: {self.imports_dir}")
            return results

        # Find all CSV files
        csv_files = sorted(
            [f for f in os.listdir(self.imports_dir) if f.endswith(".csv")]
        )

        if not csv_files:
            logger.info("No CSV files found in imports directory")
            return results

        logger.info(f"Found {len(csv_files)} CSV file(s) to process")

        for filename in csv_files:
            filepath = os.path.join(self.imports_dir, filename)
            result = self._process_file(filepath, filename)
            results["details"].append(result)

            if result["status"] == "success":
                results["processed"] += 1
            elif result["status"] == "failed":
                results["failed"] += 1
            else:
                results["skipped"] += 1

        # Log summary
        self._log_summary(results)

        # Call success callback if any imports succeeded
        if results["processed"] > 0 and self.on_success_callback:
            logger.debug(
                f"Calling success callback after importing {results['processed']} file(s)"
            )
            self.on_success_callback()

        return results

    def _process_file(self, filepath, filename):
        """
        Process a single CSV file.

        Args:
            filepath (str): Full path to CSV file
            filename (str): Name of CSV file

        Returns:
            dict: Result of processing
        """
        result = {
            "filename": filename,
            "status": "unknown",
            "items_imported": 0,
            "errors": [],
        }

        # Validate CSV
        is_valid, errors, df = CSVValidator.validate_file(filepath)

        if not is_valid:
            logger.warning(f"Validation failed for {filename}: {errors}")
            result["status"] = "failed"
            result["errors"] = errors
            self._move_file(filepath, self.failed_dir, result)
            return result

        # Try to import
        try:
            items_imported = self._import_dataframe(df)
            result["status"] = "success"
            result["items_imported"] = items_imported
            logger.info(f"Successfully imported {items_imported} items from {filename}")

            # Move to processed
            self._move_file(filepath, self.processed_dir, result)

        except Exception as e:
            logger.error(f"Import failed for {filename}: {str(e)}")
            result["status"] = "failed"
            result["errors"] = [str(e)]
            self._move_file(filepath, self.failed_dir, result)

        return result

    def _import_dataframe(self, df):
        """
        Import items from DataFrame into repository.

        Args:
            df (pd.DataFrame): Validated inventory data

        Returns:
            int: Number of items imported

        Raises:
            Exception: If import fails
        """
        imported_count = 0

        for _, row in df.iterrows():
            item_id = int(row["item_id"])
            item_name = row["item_name"]
            quantity = int(row["quantity"])
            location = row["location"]

            # Check if item already exists
            if self.repository.item_exists(item_id):
                # Update existing item
                logger.debug(
                    f"Item {item_id} already exists, updating quantity to {quantity}"
                )
                # Get current quantity
                current_item = self.repository.get_item(item_id)
                current_qty = current_item.current
                diff = quantity - current_qty

                if diff > 0:
                    self.repository.add_stock(item_id, diff)
                elif diff < 0:
                    self.repository.remove_stock(item_id, -diff)

                # Update name and location if different
                self.repository.db.execute_insert(
                    """
                    UPDATE inventory_items
                    SET item_name = ?, location = ?
                    WHERE item_id = ?
                    """,
                    (item_name, location, item_id),
                )

            else:
                # Create new item
                import datetime

                timestamp = datetime.datetime.now().isoformat()
                self.repository.db.execute_insert(
                    """
                    INSERT INTO inventory_items
                    (item_id, item_name, current, location, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item_id, item_name, quantity, location, timestamp),
                )
                # Add to cache
                from repository import InventoryItem

                self.repository.items[item_id] = InventoryItem(
                    item_id, item_name, quantity, location
                )
                logger.debug(
                    f"Created new item {item_id} ({item_name}) with qty {quantity}"
                )

            imported_count += 1

        return imported_count

    def _move_file(self, source_path, dest_dir, result):
        """
        Move file to processed or failed directory.

        Args:
            source_path (str): Source file path
            dest_dir (str): Destination directory
            result (dict): Import result details
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(source_path)
            name, ext = os.path.splitext(filename)

            # Create timestamped filename
            new_filename = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(dest_dir, new_filename)

            shutil.move(source_path, dest_path)
            logger.info(f"Moved {filename} to {dest_dir}")

        except Exception as e:
            logger.error(f"Failed to move file {source_path}: {str(e)}")

    def _log_summary(self, results):
        """
        Log import summary.

        Args:
            results (dict): Import results summary
        """
        summary = (
            f"Import Summary: {results['processed']} success, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )
        logger.info(summary)

        for detail in results["details"]:
            if detail["status"] == "failed":
                logger.warning(f"  {detail['filename']}: {', '.join(detail['errors'])}")
            elif detail["status"] == "success":
                logger.info(f"  {detail['filename']}: {detail['items_imported']} items")
