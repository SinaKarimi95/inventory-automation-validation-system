"""Audit Queries - Compliance & Reporting

Provides SQL-based queries for audit trails, compliance reports,
and system validation. Read-only access to transaction history.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict


class InventoryAuditor:
    """Generates audit reports and compliance queries."""

    def __init__(self, db_connection):
        """
        Initialize auditor with database connection.

        Args:
            db_connection: sqlite3 connection
        """
        self.conn = db_connection

    def get_activity_log(self, item_id=None, hours=24) -> List[Dict]:
        """
        Get recent activity for items (add/remove operations).

        Args:
            item_id (int): Filter by item (optional)
            hours (int): Look back this many hours (default 24)

        Returns:
            list: List of transaction dictionaries
        """
        cursor = self.conn.cursor()

        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        if item_id:
            query = """
                SELECT
                    it.transaction_id,
                    ii.item_id,
                    ii.item_name,
                    it.action,
                    it.quantity,
                    it.timestamp
                FROM inventory_transactions it
                JOIN inventory_items ii ON it.item_id = ii.item_id
                WHERE it.item_id = ? AND it.timestamp > ?
                ORDER BY it.timestamp DESC
            """
            cursor.execute(query, (item_id, cutoff_time))
        else:
            query = """
                SELECT
                    it.transaction_id,
                    ii.item_id,
                    ii.item_name,
                    it.action,
                    it.quantity,
                    it.timestamp
                FROM inventory_transactions it
                JOIN inventory_items ii ON it.item_id = ii.item_id
                WHERE it.timestamp > ?
                ORDER BY it.timestamp DESC
            """
            cursor.execute(query, (cutoff_time,))

        results = cursor.fetchall()
        return [
            {
                "transaction_id": r[0],
                "item_id": r[1],
                "item_name": r[2],
                "action": r[3],
                "quantity": r[4],
                "timestamp": r[5],
            }
            for r in results
        ]

    def get_stock_movements(self, item_id, days=7) -> Dict:
        """
        Analyze stock movements for a specific item.

        Args:
            item_id (int): Item to analyze
            days (int): Look back this many days

        Returns:
            dict: Summary of add/remove with totals
        """
        cursor = self.conn.cursor()

        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT
                action,
                COUNT(*) as count,
                SUM(quantity) as total
            FROM inventory_transactions
            WHERE item_id = ? AND timestamp > ?
            GROUP BY action
        """

        cursor.execute(query, (item_id, cutoff_time))
        results = cursor.fetchall()

        movements = {
            "item_id": item_id,
            "period_days": days,
            "add": {"count": 0, "total": 0},
            "remove": {"count": 0, "total": 0},
        }

        for action, count, total in results:
            if action == "add":
                movements["add"] = {"count": count, "total": total}
            elif action == "remove":
                movements["remove"] = {"count": count, "total": total}

        return movements

    def get_inventory_status(self) -> List[Dict]:
        """
        Get current inventory status for all items.

        Returns:
            list: Items with current quantity and location
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                item_id,
                item_name,
                current,
                location,
                updated_at
            FROM inventory_items
            ORDER BY item_id
        """

        cursor.execute(query)
        results = cursor.fetchall()

        return [
            {
                "item_id": r[0],
                "item_name": r[1],
                "current": r[2],
                "location": r[3],
                "updated_at": r[4],
            }
            for r in results
        ]

    def get_low_stock_items(self, threshold=50) -> List[Dict]:
        """
        Get items with low stock (below threshold).

        Args:
            threshold (int): Stock level threshold

        Returns:
            list: Items below threshold
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                item_id,
                item_name,
                current,
                location
            FROM inventory_items
            WHERE current < ?
            ORDER BY current
        """

        cursor.execute(query, (threshold,))
        results = cursor.fetchall()

        return [
            {
                "item_id": r[0],
                "item_name": r[1],
                "current": r[2],
                "location": r[3],
            }
            for r in results
        ]

    def get_transaction_count_by_date(self) -> List[Dict]:
        """
        Get transaction count grouped by date.

        Returns:
            list: Daily transaction counts
        """
        cursor = self.conn.cursor()

        query = """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN action = 'add' THEN quantity ELSE 0 END) as total_added,
                SUM(CASE WHEN action = 'remove' THEN quantity ELSE 0 END) as total_removed
            FROM inventory_transactions
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """

        cursor.execute(query)
        results = cursor.fetchall()

        return [
            {
                "date": r[0],
                "transaction_count": r[1],
                "total_added": r[2] or 0,
                "total_removed": r[3] or 0,
            }
            for r in results
        ]

    def export_audit_report(self, filename="audit_report.txt") -> str:
        """
        Generate a comprehensive audit report.

        Args:
            filename (str): Output filename

        Returns:
            str: Report content
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("INVENTORY SYSTEM AUDIT REPORT")
        report_lines.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        report_lines.append("=" * 80)

        # Inventory Status
        report_lines.append("\n[1] CURRENT INVENTORY STATUS")
        report_lines.append("-" * 80)
        status = self.get_inventory_status()
        if status:
            for item in status:
                report_lines.append(
                    f"Item {item['item_id']:3d} | {item['item_name']:20s} | Qty: {item['current']:5d} | Loc: {item['location']}"
                )
        else:
            report_lines.append("No items in inventory")

        # Low Stock Alert
        report_lines.append("\n[2] LOW STOCK ITEMS (threshold: 50)")
        report_lines.append("-" * 80)
        low_stock = self.get_low_stock_items(threshold=50)
        if low_stock:
            for item in low_stock:
                report_lines.append(
                    f"[ALERT] Item {item['item_id']:3d} | {item['item_name']:20s} | Qty: {item['current']:5d} | Loc: {item['location']}"
                )
        else:
            report_lines.append("No low stock items detected")

        # Recent Activity
        report_lines.append("\n[3] RECENT ACTIVITY (Last 24 hours)")
        report_lines.append("-" * 80)
        activity = self.get_activity_log(hours=24)
        if activity:
            for txn in activity[:10]:  # Show last 10
                report_lines.append(
                    f"{txn['timestamp']} | Item {txn['item_id']:3d} | {txn['action'].upper():6s} {txn['quantity']:3d} units"
                )
            if len(activity) > 10:
                report_lines.append(f"... and {len(activity) - 10} more transactions")
        else:
            report_lines.append("No activity in last 24 hours")

        # Daily Summary
        report_lines.append("\n[4] DAILY TRANSACTION SUMMARY (Last 7 days)")
        report_lines.append("-" * 80)
        daily = self.get_transaction_count_by_date()
        if daily:
            for day in daily[:7]:
                report_lines.append(
                    f"{day['date']} | Transactions: {day['transaction_count']:3d} | Added: {day['total_added']:5d} | Removed: {day['total_removed']:5d}"
                )
        else:
            report_lines.append("No transaction history available")

        report_lines.append("\n" + "=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Write to file
        with open(filename, "w") as f:
            f.write(report_content)

        return report_content
