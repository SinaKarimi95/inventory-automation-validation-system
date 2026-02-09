"""Validation Functions - QA-Friendly & Testable

Provides reusable validation for inventory operations.
All functions are pure (no side effects) for easy testing.
"""

import logging
from typing import List, Tuple, Optional

logger = logging.getLogger("inventory_system")


def validate_item_id(item_id) -> Tuple[bool, Optional[str]]:
    """
    Validate item ID format.

    Args:
        item_id: Value to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        int_id = int(item_id)
        if int_id <= 0:
            return False, "Item ID must be positive"
        return True, None
    except (ValueError, TypeError):
        return False, "Item ID must be an integer"


def validate_item_name(name) -> Tuple[bool, Optional[str]]:
    """
    Validate item name.

    Args:
        name: Value to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(name, str):
        return False, "Item name must be text"

    name = name.strip()
    if len(name) == 0:
        return False, "Item name cannot be empty"

    if len(name) > 255:
        return False, "Item name too long (max 255 characters)"

    return True, None


def validate_quantity(quantity) -> Tuple[bool, Optional[str]]:
    """
    Validate quantity value.

    Args:
        quantity: Value to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        int_qty = int(quantity)
        if int_qty < 0:
            return False, "Quantity cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, "Quantity must be an integer"


def validate_location(location) -> Tuple[bool, Optional[str]]:
    """
    Validate location string.

    Args:
        location: Value to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(location, str):
        return False, "Location must be text"

    location = location.strip()
    if len(location) == 0:
        return False, "Location cannot be empty"

    if len(location) > 255:
        return False, "Location too long (max 255 characters)"

    return True, None


def validate_stock_operation(
    current_qty, operation_qty, operation_type
) -> Tuple[bool, Optional[str]]:
    """
    Validate a stock add/remove operation.

    Args:
        current_qty (int): Current quantity on hand
        operation_qty (int): Quantity being added/removed
        operation_type (str): 'add' or 'remove'

    Returns:
        tuple: (is_valid, error_message)
    """
    # Validate operation type
    if operation_type not in ("add", "remove"):
        return False, f"Invalid operation: {operation_type}"

    # Validate quantities
    if not isinstance(current_qty, int) or current_qty < 0:
        return False, "Current quantity must be non-negative integer"

    if not isinstance(operation_qty, int) or operation_qty <= 0:
        return False, "Operation quantity must be positive integer"

    # Check for sufficient stock on remove
    if operation_type == "remove" and current_qty < operation_qty:
        return False, f"Insufficient stock (have {current_qty}, need {operation_qty})"

    # Check for overflow risk
    if operation_type == "add":
        new_qty = current_qty + operation_qty
        if new_qty > 999999999:  # Reasonable upper bound
            return False, "Operation would exceed maximum quantity"

    return True, None


def validate_item_batch(items: List[dict]) -> Tuple[bool, List[str]]:
    """
    Validate a batch of items for import.

    Args:
        items (list): List of item dictionaries

    Returns:
        tuple: (all_valid, list_of_errors)
    """
    errors = []

    if not items:
        return False, ["No items provided"]

    seen_ids = set()

    for idx, item in enumerate(items):
        row_errors = []

        # Validate each field
        if "item_id" not in item:
            row_errors.append("Missing item_id")
        else:
            is_valid, error = validate_item_id(item["item_id"])
            if not is_valid:
                row_errors.append(f"item_id: {error}")
            else:
                # Check for duplicates within batch
                item_id = int(item["item_id"])
                if item_id in seen_ids:
                    row_errors.append(f"Duplicate item_id: {item_id}")
                seen_ids.add(item_id)

        if "item_name" not in item:
            row_errors.append("Missing item_name")
        else:
            is_valid, error = validate_item_name(item["item_name"])
            if not is_valid:
                row_errors.append(f"item_name: {error}")

        if "quantity" not in item:
            row_errors.append("Missing quantity")
        else:
            is_valid, error = validate_quantity(item["quantity"])
            if not is_valid:
                row_errors.append(f"quantity: {error}")

        if "location" not in item:
            row_errors.append("Missing location")
        else:
            is_valid, error = validate_location(item["location"])
            if not is_valid:
                row_errors.append(f"location: {error}")

        # Add row errors to main error list
        if row_errors:
            errors.append(f"Row {idx + 1}: {'; '.join(row_errors)}")

    return len(errors) == 0, errors


def validate_inventory_consistency(db_connection) -> Tuple[bool, List[str]]:
    """
    Check database for consistency issues.

    Args:
        db_connection: sqlite3 connection object

    Returns:
        tuple: (is_consistent, list_of_issues)
    """
    issues = []

    try:
        cursor = db_connection.cursor()

        # Check for negative quantities
        cursor.execute(
            "SELECT item_id, item_name, current FROM inventory_items WHERE current < 0"
        )
        negative_items = cursor.fetchall()
        if negative_items:
            for item in negative_items:
                issues.append(
                    f"Item {item[0]} ({item[1]}) has negative quantity: {item[2]}"
                )

        # Check for orphaned transactions (item deleted but transactions remain)
        cursor.execute(
            """
            SELECT DISTINCT it.item_id FROM inventory_transactions it
            LEFT JOIN inventory_items ii ON it.item_id = ii.item_id
            WHERE ii.item_id IS NULL
            """
        )
        orphoned = cursor.fetchall()
        if orphoned:
            for orphan_id in orphoned:
                issues.append(
                    f"Orphaned transactions found for deleted item {orphan_id[0]}"
                )

        # Check for items with no name
        cursor.execute(
            "SELECT item_id FROM inventory_items WHERE item_name IS NULL OR item_name = ''"
        )
        unnamed = cursor.fetchall()
        if unnamed:
            for item_id in unnamed:
                issues.append(f"Item {item_id[0]} has no name")

    except Exception as e:
        issues.append(f"Error during consistency check: {str(e)}")

    return len(issues) == 0, issues
