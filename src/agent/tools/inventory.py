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
        return f"Added {name} ({unit}) at ${unit_price}/{unit}, min alert: {min_alert} {unit}."
    except IntegrityError:
        db.rollback()
        return f"Error: Item '{name}' already exists."
    finally:
        db.close()


@tool
def check_stock(item_name: str):
    """Checks the current quantity of a specific inventory item."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Item '{item_name}' not found in inventory."
        alert_status = " [LOW STOCK]" if item.min_alert > 0 and item.quantity <= item.min_alert else ""
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
            return f"Item '{item_name}' not found."
        new_quantity = item.quantity + quantity_change
        if new_quantity < 0:
            return (
                f"Error: Cannot reduce stock below zero. "
                f"Current: {item.quantity} {item.unit}, requested change: {quantity_change}"
            )
        item.quantity = new_quantity
        log = InventoryLog(
            ingredient_id=item.id,
            change_amount=quantity_change,
            reason=reason
        )
        db.add(log)
        db.commit()
        return f"Updated {item.name}. New quantity: {item.quantity} {item.unit}"
    finally:
        db.close()


@tool
def list_inventory():
    """Lists all items in the inventory with stock levels and alerts."""
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).all()
        if not items:
            return "Inventory is empty."
        lines = []
        for i in items:
            alert = " [LOW]" if i.min_alert > 0 and i.quantity <= i.min_alert else ""
            lines.append(f"- {i.name}: {i.quantity} {i.unit} (${i.unit_price}/{i.unit}){alert}")
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
            return f"Item '{item_name}' not found."
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
        return f"Updated item '{display_name}' successfully."
    except IntegrityError:
        db.rollback()
        return f"Error: Item name '{new_name}' already exists."
    finally:
        db.close()


@tool
def delete_inventory_item(item_name: str):
    """Permanently deletes an inventory item and its related recipes and logs."""
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name == item_name).first()
        if not item:
            return f"Item '{item_name}' not found."
        db.delete(item)
        db.commit()
        return f"Deleted '{item_name}' from inventory."
    finally:
        db.close()
