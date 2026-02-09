"""Database Layer - SQLite Management

Handles database schema creation, initialization, and data persistence.
Provides the primary data access layer with audit trail support.
"""

import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger("inventory_system")


class InventoryDatabase:
    """
    Manages SQLite database for inventory system.
    Handles schema creation, initialization, and data access.
    """

    def __init__(self, db_path):
        """
        Initialize database connection.

        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._connect()
        self._create_schema()

    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Return rows as dicts
            logger.debug(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.connection.cursor()

        try:
            # Create inventory_items table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_items (
                    item_id INTEGER PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    current INTEGER NOT NULL DEFAULT 0,
                    location TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # Create inventory_transactions (audit trail)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('add', 'remove')),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    timestamp TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
                )
                """
            )

            self.connection.commit()
            logger.debug("Database schema created successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to create schema: {e}")
            raise

    def get_connection(self):
        """
        Get database connection for direct SQL queries.

        Returns:
            sqlite3.Connection: Database connection
        """
        return self.connection

    def execute(self, query, params=None):
        """
        Execute a query and return all results.

        Args:
            query (str): SQL query
            params (tuple): Query parameters

        Returns:
            list: List of rows as sqlite3.Row objects
        """
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

    def execute_insert(self, query, params):
        """
        Execute an insert/update/delete query.

        Args:
            query (str): SQL query
            params (tuple): Query parameters

        Returns:
            int: Last inserted row ID
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.lastrowid

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.debug("Database connection closed")

    def migrate_from_csv(self, csv_path):
        """
        Migrate inventory data from CSV to SQLite.
        Used for initial data import or one-time migration.

        Args:
            csv_path (str): Path to CSV file

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            Exception: If migration fails
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)
            cursor = self.connection.cursor()
            timestamp = datetime.now().isoformat()

            # Check if data already exists
            cursor.execute("SELECT COUNT(*) as count FROM inventory_items")
            count = cursor.fetchone()[0]

            if count > 0:
                logger.info("Database already contains items, skipping CSV migration")
                return

            # Insert items from CSV
            for _, row in df.iterrows():
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO inventory_items
                    (item_id, item_name, current, location, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["item_id"],
                        row["item_name"],
                        row["current"],
                        row["location"],
                        timestamp,
                    ),
                )

            self.connection.commit()
            logger.info(f"Migrated {len(df)} items from CSV to database")

        except Exception as e:
            logger.error(f"CSV migration failed: {e}")
            raise

    def get_all_items(self):
        """
        Get all inventory items from database.

        Returns:
            list: List of rows (item_id, item_name, current, location, updated_at)
        """
        return self.execute("SELECT * FROM inventory_items ORDER BY item_id")

    def get_item(self, item_id):
        """
        Get a single item by ID.

        Args:
            item_id (int): Item ID

        Returns:
            sqlite3.Row or None: Item row if found
        """
        results = self.execute(
            "SELECT * FROM inventory_items WHERE item_id = ?", (item_id,)
        )
        return results[0] if results else None

    def item_exists(self, item_id):
        """
        Check if an item exists.

        Args:
            item_id (int): Item ID

        Returns:
            bool: True if item exists
        """
        result = self.execute(
            "SELECT COUNT(*) as count FROM inventory_items WHERE item_id = ?",
            (item_id,),
        )
        return result[0]["count"] > 0

    def update_item_quantity(self, item_id, quantity):
        """
        Update an item's current quantity.

        Args:
            item_id (int): Item ID
            quantity (int): New quantity

        Raises:
            ValueError: If quantity would be negative
        """
        if quantity < 0:
            raise ValueError(f"Quantity cannot be negative: {quantity}")

        timestamp = datetime.now().isoformat()
        self.execute_insert(
            """
            UPDATE inventory_items
            SET current = ?, updated_at = ?
            WHERE item_id = ?
            """,
            (quantity, timestamp, item_id),
        )

    def record_transaction(self, item_id, action, quantity, notes=None):
        """
        Record a transaction in the audit trail.

        Args:
            item_id (int): Item ID
            action (str): 'add' or 'remove'
            quantity (int): Quantity involved
            notes (str): Optional notes

        Raises:
            ValueError: If action is invalid or quantity is invalid
        """
        if action not in ("add", "remove"):
            raise ValueError(f"Invalid action: {action}")

        if quantity <= 0:
            raise ValueError(f"Quantity must be positive: {quantity}")

        timestamp = datetime.now().isoformat()
        self.execute_insert(
            """
            INSERT INTO inventory_transactions
            (item_id, action, quantity, timestamp, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, action, quantity, timestamp, notes),
        )

    def get_transaction_history(self, item_id=None, limit=None):
        """
        Get transaction history for auditing.

        Args:
            item_id (int): Filter by item ID (optional)
            limit (int): Maximum number of records to return (optional)

        Returns:
            list: List of transactions ordered by timestamp DESC
        """
        query = "SELECT * FROM inventory_transactions"
        params = []

        if item_id:
            query += " WHERE item_id = ?"
            params.append(item_id)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        return self.execute(query, params if params else None)
