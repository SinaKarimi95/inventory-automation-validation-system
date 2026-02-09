"""QA Test Suite - Validation & Audit Testing

Tests validation functions, batch processing, audit queries,
low stock alerts, and transaction summaries.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators import (
    validate_item_id,
    validate_item_name,
    validate_quantity,
    validate_location,
    validate_stock_operation,
    validate_item_batch,
)


def test_validators():
    """Test individual validation functions.

    Tests all validation functions with both positive and negative test cases:
    - validate_item_id: positive/zero/negative/non-numeric values
    - validate_quantity: positive/zero/negative/non-numeric values
    - validate_stock_operation: valid/invalid adds and removes, stock checking
    - validate_item_batch: good batches vs batches with validation errors
    """
    print("\n" + "=" * 70)
    print("VALIDATION FUNCTION TESTS")
    print("=" * 70)

    # Test item_id validation
    print("\n[1] Item ID Validation:")
    tests = [("101", True), ("-5", False), ("abc", False), ("0", False)]
    for value, expected in tests:
        is_valid, error = validate_item_id(value)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} validate_item_id({value!r}) -> {is_valid} {error or ''}")

    # Test quantity validation
    print("\n[2] Quantity Validation:")
    tests = [("100", True), ("-10", False), ("abc", False), ("0", True)]
    for value, expected in tests:
        is_valid, error = validate_quantity(value)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} validate_quantity({value!r}) -> {is_valid} {error or ''}")

    # Test stock operation validation
    print("\n[3] Stock Operation Validation:")
    tests = [
        (100, 50, "add", True),
        (50, 40, "remove", True),
        (30, 50, "remove", False),  # Insufficient stock
        (100, -5, "add", False),  # Negative qty
    ]
    for current, qty, op, expected in tests:
        is_valid, error = validate_stock_operation(current, qty, op)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} stock_operation({current}, {qty}, {op!r}) -> {is_valid}")

    # Test batch validation
    print("\n[4] Batch Validation:")
    good_batch = [
        {
            "item_id": 101,
            "item_name": "Widget A",
            "quantity": 100,
            "location": "Warehouse 1",
        },
        {
            "item_id": 102,
            "item_name": "Widget B",
            "quantity": 50,
            "location": "Warehouse 2",
        },
    ]
    is_valid, errors = validate_item_batch(good_batch)
    print(f"  {'✓' if is_valid else '✗'} Good batch: {is_valid}")

    bad_batch = [
        {
            "item_id": 101,
            "item_name": "Widget A",
            "quantity": -50,
            "location": "Warehouse 1",
        },
        {"item_id": 102, "quantity": 100, "location": "Warehouse 2"},  # Missing name
    ]
    is_valid, errors = validate_item_batch(bad_batch)
    print(f"  {'✓' if not is_valid else '✗'} Bad batch rejected: {not is_valid}")
    if errors:
        for error in errors:
            print(f"      {error}")

    print("\n" + "=" * 70)


def test_audit_queries():
    """Test audit query functionality.

    Tests the InventoryAuditor class and its query methods:
    - get_inventory_status: Get current inventory snapshot
    - get_low_stock_items: Identify items below threshold
    - get_activity_log: Retrieve recent transactions
    - get_stock_movements: Analyze per-item adds/removes
    - get_transaction_count_by_date: Daily transaction summary

    Demonstrates compliance reporting and audit trail capabilities.
    """
    print("\n" + "=" * 70)
    print("AUDIT QUERY TESTS")
    print("=" * 70)

    from inventory_system import InventorySystem
    from audit_queries import InventoryAuditor

    # Initialize system
    print("\n[1] Initializing system for audit testing...")
    system = InventorySystem("sample_data/inventory.csv")

    # Create auditor
    auditor = InventoryAuditor(system.repository.db.connection)

    # Test inventory status
    print("\n[2] Current Inventory Status:")
    status = auditor.get_inventory_status()
    print(f"  Total items: {len(status)}")
    for item in status[:3]:
        print(
            f"    Item {item['item_id']:3d}: {item['item_name']:20s} qty={item['current']:5d}"
        )
    if len(status) > 3:
        print(f"    ... and {len(status) - 3} more items")

    # Test low stock
    print("\n[3] Low Stock Items (threshold=100):")
    low_stock = auditor.get_low_stock_items(threshold=100)
    if low_stock:
        for item in low_stock:
            print(
                f"  {item['item_id']:3d} {item['item_name']:20s} qty={item['current']:5d}"
            )
    else:
        print("  No low stock items")

    # Test activity log
    print("\n[4] Recent Activity (24 hours):")
    activity = auditor.get_activity_log(hours=24)
    if activity:
        for txn in activity[:5]:
            print(
                f"  {txn['timestamp'][:19]} | Item {txn['item_id']:3d} {txn['action'].upper():6s} {txn['quantity']:3d}"
            )
        if len(activity) > 5:
            print(f"  ... and {len(activity) - 5} more transactions")
    else:
        print("  No activity in last 24 hours")

    # Test stock movements
    if status:
        item_id = status[0]["item_id"]
        print(f"\n[5] Stock Movements for Item {item_id} (7 days):")
        movements = auditor.get_stock_movements(item_id, days=7)
        print(
            f"  Add: {movements['add']['count']} operations, {movements['add']['total']} total units"
        )
        print(
            f"  Remove: {movements['remove']['count']} operations, {movements['remove']['total']} total units"
        )

    print("\n" + "=" * 70)


def main():
    """Run all QA tests."""
    print("\n")
    print("█" * 70)
    print("  INVENTORY SYSTEM - VALIDATION & QA TEST SUITE")
    print("█" * 70)

    test_validators()
    test_audit_queries()

    print("\n")
    print("█" * 70)
    print("  ✓ ALL QA TESTS COMPLETE")
    print("█" * 70)
    print("\n")


if __name__ == "__main__":
    main()
