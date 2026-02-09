"""Inventory Management System - Main Application

Provides the user interface and business logic layer for the inventory system.
Handles user interactions, logging configuration, and integrates with the data access layer.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import matplotlib.pyplot as plt
from repository import InventoryRepository

# Application paths and directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_FILE = os.path.join(BASE_DIR, "sample_data", "inventory.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def configure_logging():
    """Configure Python logging with rotating file handler.

    Sets up a two-sink logging configuration:
    - File: All DEBUG+ events with 5MB rotation and 3 backups
    - Console: INFO+ events only for user visibility

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("inventory_system")
    logger.setLevel(logging.DEBUG)

    # Configure file handler: rotate when 5MB reached, keep 3 old files
    log_file = os.path.join(LOG_DIR, "inventory_system.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)  # File captures all events

    # Configure console handler: only show INFO and above for readability
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console shows INFO+ only

    # Create consistent formatter for both handlers
    # Format: timestamp - logger_name - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = configure_logging()


class InventorySystem:
    """Business logic and UI layer for inventory management.

    Handles user interface, coordinates with data access layer (repository),
    manages logging, and orchestrates inventory operations.
    """

    def __init__(self, inventory_file):
        """Initialize system with repository backing.

        Args:
            inventory_file (str): Path to CSV file for initial data
        """
        self.repository = InventoryRepository(inventory_file)
        logger.info(f"Inventory system initialized with: {inventory_file}")

    def log_action(self, message):
        """Log an action using the configured logger.

        Args:
            message (str): Action description to log
        """
        logger.info(message)

    def display_inventory(self):
        """Display current inventory data and generate bar chart visualization.

        Shows inventory DataFrame with columns: item_id, item_name, current,
        stock_in, stock_out, location. Also creates bar chart visualization.
        """
        print("\nCurrent Inventory:")
        df = self.repository.get_all_items_dataframe()

        # Ensure optional columns exist so display doesn't crash
        for col in ("stock_in", "stock_out"):
            if col not in df.columns:
                df[col] = 0

        if df.empty:
            print("No inventory data available.")
            # Still update chart (creates an empty/placeholder chart)
            self.plot_inventory(df)
            return

        print(
            df[
                ["item_id", "item_name", "current", "stock_in", "stock_out", "location"]
            ].to_string(index=False)
        )
        self.plot_inventory(df)

    def plot_inventory(self, df):
        """Generate and save bar chart of current inventory levels.

        Creates a matplotlib bar chart showing item names vs current quantities.
        Saves chart to screenshots/inventory_levels.png.

        Args:
            df (pd.DataFrame): DataFrame with item_name and current quantity columns
        """
        # Dynamically choose chart layout based on number of items
        num_items = len(df) if df is not None else 0

        if num_items == 0:
            plt.figure(figsize=(6, 3))
            plt.text(0.5, 0.5, "No inventory data", ha="center", va="center")
            plt.title("Inventory Levels")
            output_path = os.path.join(SCREENSHOT_DIR, "inventory_levels.png")
            plt.savefig(output_path)
            plt.close()
            logger.debug(f"Updated inventory chart (placeholder): {output_path}")
            return

        # Prepare data defensively
        item_names = (
            df["item_name"] if "item_name" in df.columns else df.index.astype(str)
        )
        quantities = (
            df["current"] if "current" in df.columns else pd.Series([0] * num_items)
        )

        # If many items, use horizontal bar chart for readability
        if num_items > 12:
            height = max(6, 0.35 * num_items)
            plt.figure(figsize=(10, height))
            y_pos = range(num_items)
            plt.barh(y_pos, quantities, align="center")
            plt.yticks(y_pos, item_names, fontsize=9)
            plt.gca().invert_yaxis()
            plt.xlabel("Current Quantity")
            plt.title("Inventory Levels")
        else:
            # Vertical chart with rotated x labels when needed
            width = max(8, 0.5 * num_items)
            plt.figure(figsize=(width, 4))
            plt.bar(item_names, quantities)
            plt.title("Inventory Levels")
            plt.xlabel("Item")
            plt.ylabel("Current Quantity")
            plt.xticks(rotation=45, ha="right", fontsize=9)
        plt.title("Inventory Levels")
        plt.xlabel("Item")
        plt.ylabel("Current Quantity")
        plt.tight_layout()

        output_path = os.path.join(SCREENSHOT_DIR, "inventory_levels.png")
        plt.savefig(output_path)
        plt.close()
        logger.debug(f"Updated inventory chart: {output_path}")

    def update_chart(self):
        """Regenerate the inventory chart from current data.

        Called after CSV imports or manual updates to refresh visualization.
        """
        df = self.repository.get_all_items_dataframe()
        self.plot_inventory(df)
        logger.info("Inventory chart updated")

    def check_in_out(self):
        """Handle stock add/remove operations with comprehensive validation.

        Guides user through:
        1. Scanning/entering item ID
        2. Choosing action (add/remove)
        3. Entering quantity
        4. Validates all inputs before committing
        5. Updates inventory, records transaction, logs action, refreshes display
        """
        try:
            # Get valid item ID - must be positive integer
            while True:
                raw_input = input("Scan item (enter item_id): ").strip()

                # Validate input is numeric
                if not raw_input.isdigit():
                    print("Invalid item ID. Please enter a numeric item ID.")
                    continue

                item_id = int(raw_input)

                # Check if item exists in database
                if not self.repository.item_exists(item_id):
                    print("Item ID does not exist in inventory.")
                    continue

                break

            # Get valid action - either 'add' or 'remove'
            while True:
                action = input("Action (add/remove): ").strip().lower()
                if action in {"add", "remove"}:
                    break
                print("Invalid action. Please enter only 'add' or 'remove'.")

            # Get quantity - must be positive integer
            qty_input = input("Quantity: ").strip()
            if not qty_input.isdigit() or int(qty_input) <= 0:
                print("Quantity must be a positive number.")
                return

            qty = int(qty_input)

            # Fetch item details before operation
            # Repository will handle all validation and persist changes
            item = self.repository.get_item(item_id)
            try:
                # Execute operation (add or remove) - repository handles validation
                if action == "add":
                    self.repository.add_stock(item_id, qty)
                    self.log_action(
                        f"Added {qty} units to item {item_id} ({item.name})"
                    )
                    print(f"Added {qty} units to {item.name}")

                elif action == "remove":
                    self.repository.remove_stock(item_id, qty)
                    self.log_action(
                        f"Removed {qty} units from item {item_id} ({item.name})"
                    )
                    print(f"Removed {qty} units from {item.name}")

                # Persist changes and refresh visualization
                # Note: For SQLite backend, save() is a no-op (auto-commit)
                self.repository.save()
                df = self.repository.get_all_items_dataframe()
                self.plot_inventory(df)

            except ValueError as e:
                # Repository validation failed (e.g., insufficient stock)
                print(f"Operation failed: {e}")

        except Exception as e:
            # Unexpected error - log and report
            print(f"Unexpected error: {e}")
            logger.error(f"Unexpected error in check_in_out: {e}")

    def run(self):
        """Run interactive menu loop.

        Presents user with menu options to:
        1. Display current inventory and chart
        2. Add or remove stock from items
        3. Exit the application
        """
        while True:
            print("\n--- Inventory System ---")
            print("1. Display Inventory")
            print("2. Check-in / Check-out")
            print("3. Exit")

            choice = input("Choose an option: ").strip()

            if choice == "1":
                self.display_inventory()
            elif choice == "2":
                self.check_in_out()
            elif choice == "3":
                print("Exiting...")
                logger.info("Inventory system shutdown")
                break
            else:
                print("Invalid option.")


if __name__ == "__main__":
    # Initialize and run the inventory system with the sample data CSV
    system = InventorySystem(INVENTORY_FILE)
    system.run()
