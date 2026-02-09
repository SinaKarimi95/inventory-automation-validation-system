"""Data Access Layer for Inventory System

Provides abstraction between business logic and data storage.
Backed by SQLite with transaction audit trail.
"""

import os
import logging
import pandas as pd
from database import InventoryDatabase

logger = logging.getLogger("inventory_system")


class InventoryItem:
    """Represents a single inventory item (domain model)."""

    def __init__(self, item_id, name, current, location):
        self.item_id = item_id
        self.name = name
        self.current = current
        self.location = location


class InventoryRepository:
    """
    Handles all data persistence and retrieval.
    Backed by SQLite database with transaction history.
    """

    def __init__(self, csv_path, db_path=None):
        """
        Initialize repository with SQLite database.
        Optionally migrate from CSV on first run.

        Args:
            csv_path (str): Path to CSV file (for initial migration if needed)
            db_path (str): Path to SQLite database (default: inventory.db in same directory)
        """
        self.csv_path = csv_path

        # Set database path
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(csv_path))
            db_path = os.path.join(base_dir, "inventory.db")

        self.db_path = db_path
        self.db = InventoryDatabase(db_path)
        self.items = {}

        # Migrate from CSV if database is empty
        self._initialize_from_csv()

        # Load items into cache
        self._load_items()

    def _initialize_from_csv(self):
        """
        Migrate data from CSV to database on first run.
        Only happens if database is empty.
        """
        if os.path.exists(self.csv_path):
            try:
                self.db.migrate_from_csv(self.csv_path)
            except Exception as e:
                logger.error(f"Failed to initialize from CSV: {e}")
                # Continue anyway; database might have data from previous run

    def _load_items(self):
        """Load all items from database into in-memory cache."""
        self.items = {}
        rows = self.db.get_all_items()
        for row in rows:
            self.items[row["item_id"]] = InventoryItem(
                item_id=row["item_id"],
                name=row["item_name"],
                current=row["current"],
                location=row["location"],
            )
        logger.debug(f"Loaded {len(self.items)} items from database")

    def get_item(self, item_id):
        """
        Retrieve a single inventory item.

        Args:
            item_id (int): The item ID to retrieve

        Returns:
            InventoryItem or None if not found
        """
        return self.items.get(item_id)

    def item_exists(self, item_id):
        """
        Check if an item exists in inventory.

        Args:
            item_id (int): The item ID to check

        Returns:
            bool: True if item exists
        """
        return item_id in self.items

    def get_all_items_dataframe(self):
        """
        Get the full inventory as a DataFrame (for display/export).
        Uses cached items to build DataFrame.

        Returns:
            pd.DataFrame: Current inventory state
        """
        rows = self.db.get_all_items()
        if not rows:
            return pd.DataFrame(
                columns=[
                    "item_id",
                    "item_name",
                    "current",
                    "location",
                    "stock_in",
                    "stock_out",
                ]
            )

        # Aggregate transaction history to compute stock_in and stock_out per item
        add_rows = self.db.execute(
            "SELECT item_id, SUM(quantity) as total FROM inventory_transactions WHERE action='add' GROUP BY item_id"
        )
        remove_rows = self.db.execute(
            "SELECT item_id, SUM(quantity) as total FROM inventory_transactions WHERE action='remove' GROUP BY item_id"
        )

        adds = {r["item_id"]: r["total"] for r in add_rows} if add_rows else {}
        removes = {r["item_id"]: r["total"] for r in remove_rows} if remove_rows else {}

        data = [
            {
                "item_id": row["item_id"],
                "item_name": row["item_name"],
                "current": row["current"],
                "location": row["location"],
                "stock_in": int(adds.get(row["item_id"], 0)),
                "stock_out": int(removes.get(row["item_id"], 0)),
            }
            for row in rows
        ]

        return pd.DataFrame(data)

    def add_stock(self, item_id, quantity):
        """
        Add quantity to an item's current stock.
        Records transaction in audit trail.

        Args:
            item_id (int): The item to increase
            quantity (int): Amount to add (must be positive)

        Raises:
            ValueError: If item not found or quantity is invalid
        """
        if not self.item_exists(item_id):
            logger.error(f"Item {item_id} not found in repository")
            raise ValueError(f"Item {item_id} not found")

        if quantity <= 0:
            logger.error(f"Invalid quantity for add_stock: {quantity}")
            raise ValueError("Quantity must be positive")

        # Get current quantity
        item = self.get_item(item_id)
        new_quantity = item.current + quantity

        # Update database
        self.db.update_item_quantity(item_id, new_quantity)
        self.db.record_transaction(item_id, "add", quantity)

        # Update cache
        item.current = new_quantity
        logger.debug(
            f"Added {quantity} units to item {item_id}, new total: {new_quantity}"
        )

    def remove_stock(self, item_id, quantity):
        """
        Remove quantity from an item's current stock.
        Records transaction in audit trail.

        Args:
            item_id (int): The item to decrease
            quantity (int): Amount to remove (must be positive)

        Raises:
            ValueError: If item not found, quantity is invalid, or insufficient stock
        """
        if not self.item_exists(item_id):
            logger.error(f"Item {item_id} not found in repository")
            raise ValueError(f"Item {item_id} not found")

        if quantity <= 0:
            logger.error(f"Invalid quantity for remove_stock: {quantity}")
            raise ValueError("Quantity must be positive")

        item = self.get_item(item_id)
        current_qty = item.current

        if current_qty < quantity:
            logger.warning(
                f"Insufficient stock for item {item_id}: available={current_qty}, requested={quantity}"
            )
            raise ValueError(
                f"Insufficient stock. Available: {current_qty}, Requested: {quantity}"
            )

        # Calculate new quantity and update
        new_quantity = current_qty - quantity

        # Update database
        self.db.update_item_quantity(item_id, new_quantity)
        self.db.record_transaction(item_id, "remove", quantity)

        # Update cache
        item.current = new_quantity
        logger.debug(
            f"Removed {quantity} units from item {item_id}, new total: {new_quantity}"
        )

    def save(self):
        """
        Persist current state.
        For SQLite, this is a no-op (data is persisted automatically).
        For backward compatibility, it's kept.
        """
        logger.debug("Save called (database auto-commits)")

    def reload(self):
        """Reload inventory from database (useful for testing)."""
        logger.debug("Reloading inventory from database")
        self._load_items()

    def get_transaction_history(self, item_id=None, limit=50):
        """
        Get transaction history for auditing purposes.

        Args:
            item_id (int): Filter by item ID (optional)
            limit (int): Maximum number of records to return

        Returns:
            list: List of transactions
        """
        return self.db.get_transaction_history(item_id=item_id, limit=limit)

    def export_to_csv(self, output_path=None):
        """
        Export current inventory to CSV format.
        Useful for backups or integration with other systems.

        Args:
            output_path (str): Path to write CSV (default: original csv_path)

        Raises:
            Exception: If export fails
        """
        if output_path is None:
            output_path = self.csv_path

        try:
            df = self.get_all_items_dataframe()
            df.to_csv(output_path, index=False)
            logger.info(f"Exported {len(df)} items to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
