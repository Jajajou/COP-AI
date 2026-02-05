from datetime import datetime, timedelta
from langchain_core.tools import tool
from sqlalchemy import func
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import Sale, InventoryItem, Order, OrderItem, MenuItem


@tool
def daily_revenue(date_str: str = ""):
    """Gets total revenue and detailed item list for a specific date (YYYY-MM-DD format). Defaults to today."""
    db = SessionLocal()
    try:
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return "Lỗi: Sai định dạng ngày. Vui lòng dùng YYYY-MM-DD."
        else:
            target_date = datetime.now().date()

        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        # 1. Tổng hợp doanh thu
        order_total = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
            Order.created_at >= start, Order.created_at < end
        ).scalar()

        inv_total = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.timestamp >= start, Sale.timestamp < end, Sale.sale_type == "INVENTORY"
        ).scalar()

        quick_total = db.query(func.coalesce(func.sum(Sale.total_amount), 0)).filter(
            Sale.timestamp >= start, Sale.timestamp < end, Sale.sale_type == "QUICK"
        ).scalar()

        total = float(order_total) + float(inv_total) + float(quick_total)

        # 2. Chi tiết các món từ Menu đã bán
        menu_details = db.query(
            MenuItem.name,
            func.sum(OrderItem.quantity).label("qty"),
            func.sum(OrderItem.quantity * OrderItem.price_at_sale).label("subtotal")
        ).join(OrderItem, MenuItem.id == OrderItem.product_id)\
         .join(Order, Order.id == OrderItem.order_id)\
         .filter(Order.created_at >= start, Order.created_at < end)\
         .group_by(MenuItem.name).all()

        # 3. Chi tiết bán lẻ kho hoặc bán nhanh
        other_details = db.query(
            Sale.item_name,
            func.sum(Sale.quantity).label("qty"),
            func.sum(Sale.total_amount).label("subtotal")
        ).filter(Sale.timestamp >= start, Sale.timestamp < end, Sale.sale_type != "MENU")\
         .group_by(Sale.item_name).all()

        # 4. Tạo chuỗi phản hồi
        report = f"📊 **BÁO CÁO DOANH THU NGÀY {target_date}**\n\n"
        
        if not menu_details and not other_details:
            return report + "Hôm nay chưa có đơn hàng nào, Sếp ơi!"

        if menu_details:
            report += "☕ **Các món từ Menu:**\n"
            for row in menu_details:
                report += f"  - {row.name}: {int(row.qty)} ly | {int(row.subtotal):,} VNĐ\n"
        
        if other_details:
            report += "\n📦 **Bán lẻ kho & Khác:**\n"
            for row in other_details:
                qty_str = f"{row.qty} " if row.qty > 1 else ""
                report += f"  - {row.item_name}: {qty_str}| {int(row.subtotal):,} VNĐ\n"

        report += f"\n---\n"
        report += f"💰 **TỔNG CỘNG: {int(total):,} VNĐ**"
        
        return report
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
            return "Tất cả kho đều ổn định. Không có cảnh báo."
        lines = ["CẢNH BÁO KHO THẤP:"]
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
            return f"Không có dữ liệu bán hàng trong {days} ngày qua."
        lines = [f"Top {limit} món chạy ({days} ngày qua):"]
        for rank, row in enumerate(results, 1):
            lines.append(f"  {rank}. {row.name}: {int(row.total_qty)} ly ({int(row.total_revenue):,} VNĐ)")
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
            return f"Không có lịch sử bán hàng trong {days} ngày qua."
        lines = [f"Lịch sử bán hàng ({days} ngày qua):"]
        grand_total = 0.0
        for row in results:
            daily = float(row.daily_total or 0)
            grand_total += daily
            lines.append(f"  {row.sale_date}: {row.order_count} đơn, {int(daily):,} VNĐ")
        lines.append(f"  ---\n  Tổng cộng: {int(grand_total):,} VNĐ")
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
