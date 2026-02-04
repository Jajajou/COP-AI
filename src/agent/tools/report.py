from datetime import datetime, timedelta
from langchain_core.tools import tool
from sqlalchemy import func
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import Sale, InventoryItem, Order, OrderItem, MenuItem


@tool
def daily_revenue(date_str: str = ""):
    """Gets total revenue for a specific date (YYYY-MM-DD format). Defaults to today."""
    db = SessionLocal()
    try:
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return "Error: Invalid date format. Use YYYY-MM-DD."
        else:
            target_date = datetime.now().date()

        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        order_total = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
            Order.created_at >= start,
            Order.created_at < end
        ).scalar()

        inv_total = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.timestamp >= start,
            Sale.timestamp < end,
            Sale.sale_type == "INVENTORY"
        ).scalar()

        total = float(order_total) + float(inv_total)

        order_count = db.query(func.count(Order.id)).filter(
            Order.created_at >= start,
            Order.created_at < end
        ).scalar()

        inv_count = db.query(func.count(Sale.id)).filter(
            Sale.timestamp >= start,
            Sale.timestamp < end,
            Sale.sale_type == "INVENTORY"
        ).scalar()

        return (
            f"Revenue for {target_date}:\n"
            f"  Menu sales: ${float(order_total):.2f} ({order_count} orders)\n"
            f"  Inventory sales: ${float(inv_total):.2f} ({inv_count} transactions)\n"
            f"  Total: ${total:.2f}"
        )
    finally:
        db.close()


@tool
def stock_alerts():
    """Lists all inventory items that are at or below their minimum alert threshold."""
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).filter(
            InventoryItem.min_alert > 0,
            InventoryItem.quantity <= InventoryItem.min_alert
        ).all()
        if not items:
            return "All stock levels are healthy. No alerts."
        lines = ["LOW STOCK ALERTS:"]
        for i in items:
            lines.append(f"  - {i.name}: {i.quantity} {i.unit} (min: {i.min_alert} {i.unit})")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def top_sellers(days: int = 7, limit: int = 5):
    """Shows top selling menu items by quantity over the past N days."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)
        results = (
            db.query(
                MenuItem.name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("total_qty"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.price_at_sale), 0).label("total_revenue")
            )
            .join(OrderItem, OrderItem.product_id == MenuItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.created_at >= since)
            .group_by(MenuItem.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
            .all()
        )
        if not results:
            return f"No sales data in the past {days} days."
        lines = [f"Top {limit} sellers (past {days} days):"]
        for rank, row in enumerate(results, 1):
            lines.append(f"  {rank}. {row.name}: {int(row.total_qty)} sold (${float(row.total_revenue):.2f})")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def sales_history(days: int = 7):
    """Shows a day-by-day sales summary for the past N days."""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(days=days)

        results = (
            db.query(
                func.date(Order.created_at).label("sale_date"),
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("daily_total")
            )
            .filter(Order.created_at >= since)
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).desc())
            .all()
        )
        if not results:
            return f"No sales history in the past {days} days."
        lines = [f"Sales history (past {days} days):"]
        grand_total = 0.0
        for row in results:
            daily = float(row.daily_total or 0)
            grand_total += daily
            lines.append(f"  {row.sale_date}: {row.order_count} orders, ${daily:.2f}")
        lines.append(f"  ---\n  Grand total: ${grand_total:.2f}")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def reset_today_revenue():
    """⚠️ DANGER: Resets all revenue for TODAY.
    Deletes all Orders and Sales records created today.
    Use this only if you want to clear the day's sales to start over.
    This action CANNOT be undone.
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        # Delete Orders (cascades to OrderItems)
        deleted_orders = db.query(Order).filter(
            Order.created_at >= start,
            Order.created_at < end
        ).delete(synchronize_session=False)

        # Delete Sales (Inventory/Quick sales)
        deleted_sales = db.query(Sale).filter(
            Sale.timestamp >= start,
            Sale.timestamp < end
        ).delete(synchronize_session=False)

        db.commit()
        return f"REVENUE RESET: Deleted {deleted_orders} orders and {deleted_sales} sales records for today ({today})."
    except Exception as e:
        db.rollback()
        return f"Error resetting revenue: {e}"
    finally:
        db.close()
