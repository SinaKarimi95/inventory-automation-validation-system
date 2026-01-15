import os
import pandas as pd
import matplotlib.pyplot as plt
from utils import timestamp  # Import timestamp helper

# Base directory (works no matter where script is run)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
INVENTORY_FILE = os.path.join(BASE_DIR, "sample_data", "inventory.csv")
LOG_FILE = os.path.join(BASE_DIR, "logs", "activity.log")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Ensure directories exist
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "screenshots"), exist_ok=True)


class InventoryItem:
    """Represents a single inventory item"""

    def __init__(self, item_id, name, quantity, location):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity
        self.location = location


class InventorySystem:
    """Inventory system with check-in/out and automatic visualization"""

    def __init__(self, inventory_file):
        self.inventory_file = inventory_file
        self.load_inventory()

    def load_inventory(self):
        self.df = pd.read_csv(self.inventory_file)
        self.items = {}
        for _, row in self.df.iterrows():
            self.items[row["item_id"]] = InventoryItem(
                row["item_id"], row["item_name"], row["quantity"], row["location"]
            )

    def save_inventory(self):
        self.df.to_csv(self.inventory_file, index=False)

    def log_action(self, message):
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp()} - {message}\n")

    def display_inventory(self):
        """Print table and plot bar chart"""
        print("\nCurrent Inventory:")
        print(self.df[["item_id", "item_name", "quantity", "location"]])
        self.plot_inventory()

    def plot_inventory(self):
        """Generate and save bar chart of inventory quantities"""
        plt.figure(figsize=(8, 4))
        plt.bar(self.df["item_name"], self.df["quantity"], color="skyblue")
        plt.title("Inventory Levels")
        plt.xlabel("Item")
        plt.ylabel("Quantity")
        plt.tight_layout()
        plt.savefig(os.path.join(SCREENSHOT_DIR, "inventory_levels.png"))
        plt.show()

    def check_in_out(self):
        """Simulate QR scan workflow"""
        try:
            item_id = int(input("Scan item (enter item_id): "))
            if item_id not in self.items:
                print("Item not found in inventory.")
                return
            action = input("Action (add/remove): ").strip().lower()
            qty = int(input("Quantity: "))

            if action == "add":
                self.df.loc[self.df["item_id"] == item_id, "quantity"] += qty
                self.items[item_id].quantity += qty
                self.log_action(
                    f"Added {qty} units to item {item_id} ({self.items[item_id].name})"
                )
                print(f"Added {qty} units to {self.items[item_id].name}")
            elif action == "remove":
                self.df.loc[self.df["item_id"] == item_id, "quantity"] -= qty
                self.items[item_id].quantity -= qty
                self.log_action(
                    f"Removed {qty} units from item {item_id} ({self.items[item_id].name})"
                )
                print(f"Removed {qty} units from {self.items[item_id].name}")
            else:
                print("Invalid action.")
                return

            # Save inventory and update chart automatically
            self.save_inventory()
            self.plot_inventory()

        except ValueError:
            print("Invalid input. Please enter numbers only.")

    def run(self):
        """Main CLI loop"""
        while True:
            print("\n--- Inventory System ---")
            print("1. Display Inventory")
            print("2. Check-in/Check-out item")
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
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    system = InventorySystem(INVENTORY_FILE)
    system.run()
