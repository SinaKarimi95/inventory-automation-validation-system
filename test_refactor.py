#!/usr/bin/env python
"""Deployment Validation Tests - Architecture Verification

Ensures refactoring to SQLite is complete with no breaking changes.
Validates imports, repository interface, domain model, and architecture.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all modules import cleanly."""
    try:
        from repository import InventoryRepository, InventoryItem
        from inventory_system import InventorySystem
        from utils import timestamp

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_repository_interface():
    """Test that repository has all expected methods.

    Verifies InventoryRepository class has the complete public API needed
    for data access operations. This ensures the abstraction is properly
    maintained for potential backend swapping (e.g., SQLite to PostgreSQL).

    Returns:
        bool: True if all methods exist
    """
    from repository import InventoryRepository

    expected_methods = [
        "get_item",
        "item_exists",
        "get_all_items_dataframe",
        "add_stock",
        "remove_stock",
        "save",
        "reload",
    ]

    for method in expected_methods:
        if not hasattr(InventoryRepository, method):
            print(f"✗ InventoryRepository missing method: {method}")
            return False

    print("✓ InventoryRepository has all expected methods")
    return True


def test_inventory_item_model():
    """Test that InventoryItem is properly defined."""
    from repository import InventoryItem

    # Create a test item
    item = InventoryItem(item_id=999, name="Test Item", current=10, location="Test")

    assert item.item_id == 999
    assert item.name == "Test Item"
    assert item.current == 10
    assert item.location == "Test"

    print("✓ InventoryItem model works correctly")
    return True


def test_inventory_system_uses_repository():
    """Test that InventorySystem delegates to repository."""
    from inventory_system import InventorySystem
    import inspect

    # Check that __init__ creates a repository
    init_source = inspect.getsource(InventorySystem.__init__)
    if "self.repository" not in init_source:
        print("✗ InventorySystem.__init__ doesn't use repository")
        return False

    # Check that old CSV methods are removed
    if hasattr(InventorySystem, "load_inventory"):
        print("✗ InventorySystem still has load_inventory method (should be removed)")
        return False

    if hasattr(InventorySystem, "save_inventory"):
        print("✗ InventorySystem still has save_inventory method (should be removed)")
        return False

    print("✓ InventorySystem properly delegates to repository")
    return True


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("REFACTORING VALIDATION TESTS")
    print("=" * 60 + "\n")

    tests = [
        ("Imports", test_imports),
        ("Repository Interface", test_repository_interface),
        ("InventoryItem Model", test_inventory_item_model),
        ("InventorySystem Architecture", test_inventory_system_uses_repository),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {name} test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
