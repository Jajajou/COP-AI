from langchain_core.tools import tool
from sqlalchemy.exc import IntegrityError
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import InventoryItem, InventoryLog


@tool
def add_inventory_item(name: str, unit: str, unit_price: float, min_alert: float = 0.0):
    """Adds a new item to the inventory definition (e.g., 'Coffee Beans', 'kg', 25.0, min_alert=5.0)."""
    db = SessionLocal()
    try:
        item = InventoryItem(name=name, unit=unit, unit_price=unit_price, min_alert=min_alert)
        db.add(item)
        db.commit()
        return f"Đã thêm {name} ({unit}) với giá {int(unit_price):,} VNĐ/{unit}, cảnh báo khi dưới: {min_alert} {unit}."
    except IntegrityError:
        db.rollback()
        return f"Lỗi: Vật phẩm '{name}' đã tồn tại."
    finally:
        db.close()


@tool
def check_stock(item_name: str):
    """Checks the current quantity of a specific inventory item."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Không tìm thấy vật phẩm '{item_name}' trong kho."
        alert_status = " [SẮP HẾT HÀNG]" if item.min_alert > 0 and item.quantity <= item.min_alert else ""
        return f"{item.name}: {item.quantity} {item.unit}{alert_status}"
    finally:
        db.close()


@tool
def update_stock(item_name: str, quantity_change: float, reason: str = "manual_adjustment"):
    """Updates stock quantity. Use positive for adding stock, negative for removing.
    Reason examples: 'restock', 'waste', 'manual_adjustment'."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Không tìm thấy vật phẩm '{item_name}'."
        new_quantity = item.quantity + quantity_change
        if new_quantity < 0:
            return (
                f"Lỗi: Không thể giảm kho xuống dưới 0. "
                f"Hiện tại: {item.quantity} {item.unit}, lượng thay đổi yêu cầu: {quantity_change}"
            )
        item.quantity = new_quantity
        log = InventoryLog(
            ingredient_id=item.id,
            change_amount=quantity_change,
            reason=reason
        )
        db.add(log)
        db.commit()
        return f"Đã cập nhật {item.name}. Số lượng mới: {item.quantity} {item.unit}"
    finally:
        db.close()


@tool
def list_inventory():
    """Lists all items in the inventory with stock levels and alerts."""
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).all()
        if not items:
            return "Kho hàng trống."
        lines = []
        for i in items:
            alert = " [ÍT]" if i.min_alert > 0 and i.quantity <= i.min_alert else ""
            lines.append(f"- {i.name}: {i.quantity} {i.unit} ({int(i.unit_price):,} VNĐ/{i.unit}){alert}")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def update_inventory_item(item_name: str, new_name: str = "", new_unit: str = "", new_unit_price: float = -1, new_min_alert: float = -1):
    """Updates an existing inventory item's definition (name, unit, unit_price, min_alert).
    Only provided fields are updated. Use -1 to skip numeric fields."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Không tìm thấy vật phẩm '{item_name}'."
        if new_name:
            item.name = new_name
        if new_unit:
            item.unit = new_unit
        if new_unit_price >= 0:
            item.unit_price = new_unit_price
        if new_min_alert >= 0:
            item.min_alert = new_min_alert
        db.commit()
        display_name = new_name if new_name else item_name
        return f"Đã cập nhật vật phẩm '{display_name}' thành công."
    except IntegrityError:
        db.rollback()
        return f"Lỗi: Tên vật phẩm '{new_name}' đã tồn tại."
    finally:
        db.close()


@tool
def delete_inventory_item(item_name: str):
    """Permanently deletes an inventory item and its related recipes and logs."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Không tìm thấy vật phẩm '{item_name}'."
        db.delete(item)
        db.commit()
        return f"Đã xóa '{item_name}' khỏi kho."
    finally:
        db.close()
