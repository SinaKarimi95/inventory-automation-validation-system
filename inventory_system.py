import os
import pandas as pd
import matplotlib.pyplot as plt
from utils import timestamp

# -----------------------------
# Paths & Directories
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INVENTORY_FILE = os.path.join(BASE_DIR, "sample_data", "inventory.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "activity.log")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# -----------------------------
# Inventory Item Model
# -----------------------------


class InventoryItem:
    # Represents a single inventory item

    def __init__(self, item_id, name, current, location):
        self.item_id = item_id
        self.name = name
        self.current = current
        self.location = location


# -----------------------------
# Inventory System
# -----------------------------


class InventorySystem:
    # Inventory system with logging and visualization

    def __init__(self, inventory_file):
        self.inventory_file = inventory_file
        self.load_inventory()

    def load_inventory(self):
        # Load inventory CSV into memory
        self.df = pd.read_csv(self.inventory_file)
        self.items = {}

        for _, row in self.df.iterrows():
            self.items[row["item_id"]] = InventoryItem(
                item_id=row["item_id"],
                name=row["item_name"],
                current=row["current"],
                location=row["location"],
            )

    def save_inventory(self):
        # Persist inventory changes to CSV
        self.df.to_csv(self.inventory_file, index=False)

    def log_action(self, message):
        # Append action to log file
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp()} - {message}\n")

    # -----------------------------
    # Display & Visualization
    # -----------------------------

    def display_inventory(self):
        print("\nCurrent Inventory:")
        print(
            self.df[
                ["item_id", "item_name", "current", "stock_in", "stock_out", "location"]
            ].to_string(index=False)
        )
        self.plot_inventory()

    def plot_inventory(self):
        plt.figure(figsize=(8, 4))
        plt.bar(self.df["item_name"], self.df["current"])
        plt.title("Inventory Levels")
        plt.xlabel("Item")
        plt.ylabel("Current Quantity")
        plt.tight_layout()

        output_path = os.path.join(SCREENSHOT_DIR, "inventory_levels.png")
        plt.savefig(output_path)
        plt.close()

    # -----------------------------
    # Check-in / Check-out Workflow
    # -----------------------------

    def check_in_out(self):
        try:
            while True:
                raw_input = input("Scan item (enter item_id): ").strip()

                if not raw_input.isdigit():
                    print("Invalid item ID. Please enter a numeric item ID.")
                    continue

                item_id = int(raw_input)

                if item_id not in self.items:
                    print("Item ID does not exist in inventory.")
                    continue

                break

            if item_id not in self.items:
                print("Item not found.")
                return

            while True:
                action = input("Action (add/remove): ").strip().lower()
                if action in {"add", "remove"}:
                    break
                print("Invalid action. Please enter only 'add' or 'remove'.")

            qty = int(input("Quantity: "))

            if qty <= 0:
                print("Quantity must be positive.")
                return

            if action == "add":
                self.df.loc[self.df["item_id"] == item_id, "stock_in"] += qty
                self.df.loc[self.df["item_id"] == item_id, "current"] += qty
                self.items[item_id].current += qty

                self.log_action(
                    f"Added {qty} units to item {item_id} ({self.items[item_id].name})"
                )
                print(f"Added {qty} units to {self.items[item_id].name}")

            elif action == "remove":
                if self.items[item_id].current < qty:
                    print("Insufficient stock.")
                    return

                self.df.loc[self.df["item_id"] == item_id, "stock_out"] += qty
                self.df.loc[self.df["item_id"] == item_id, "current"] -= qty
                self.items[item_id].current -= qty

                self.log_action(
                    f"Removed {qty} units from item {item_id} ({self.items[item_id].name})"
                )
                print(f"Removed {qty} units from {self.items[item_id].name}")

            else:
                print("Invalid action.")
                return

            self.save_inventory()
            self.plot_inventory()

        except ValueError:
            print("Invalid input. Please enter numeric values.")

    # -----------------------------
    # Main Loop
    # -----------------------------

    def run(self):
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
                break
            else:
                print("Invalid option.")


# -----------------------------
# Entry Point
# -----------------------------

if __name__ == "__main__":
    system = InventorySystem(INVENTORY_FILE)
    system.run()
