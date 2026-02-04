from langchain_core.tools import tool
from sqlalchemy.exc import IntegrityError
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import MenuItem


@tool
def add_menu_item(name: str, price: float, description: str = "", category: str = "General"):
    """Adds a new item to the selling menu with optional category.
    Categories: 'Hot Drinks', 'Cold Drinks', 'Food', 'General', etc."""
    db = SessionLocal()
    try:
        item = MenuItem(name=name, price=price, description=description, category=category)
        db.add(item)
        db.commit()
        return f"Added to menu: {name} - ${price} [{category}]"
    except IntegrityError:
        db.rollback()
        return f"Error: Menu item '{name}' already exists."
    finally:
        db.close()


@tool
def get_menu(category: str = ""):
    """Retrieves the current menu. Optionally filter by category. Only shows active items."""
    db = SessionLocal()
    try:
        query = db.query(MenuItem).filter(MenuItem.is_active == True)
        if category:
            query = query.filter(MenuItem.category == category)
        items = query.all()
        if not items:
            return "No menu items found." if category else "Menu is empty."
        lines = []
        for i in items:
            desc = i.description or "No description"
            lines.append(f"- {i.name}: ${i.price} [{i.category}] ({desc})")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def update_menu_item(item_name: str, new_name: str = "", new_price: float = -1, new_description: str = "", new_category: str = ""):
    """Updates a menu item's details. Only provided fields are changed. Use -1 to skip price."""
    db = SessionLocal()
    try:
        item = db.query(MenuItem).filter(MenuItem.name == item_name).first()
        if not item:
            return f"Menu item '{item_name}' not found."
        if new_name:
            item.name = new_name
        if new_price >= 0:
            item.price = new_price
        if new_description:
            item.description = new_description
        if new_category:
            item.category = new_category
        db.commit()
        display_name = new_name if new_name else item_name
        return f"Updated menu item '{display_name}' successfully."
    except IntegrityError:
        db.rollback()
        return f"Error: Menu item name '{new_name}' already exists."
    finally:
        db.close()


@tool
def delete_menu_item(item_name: str):
    """Permanently deletes a menu item. Consider using toggle_menu_item to deactivate instead."""
    db = SessionLocal()
    try:
        item = db.query(MenuItem).filter(MenuItem.name == item_name).first()
        if not item:
            return f"Menu item '{item_name}' not found."
        db.delete(item)
        db.commit()
        return f"Deleted '{item_name}' from menu."
    finally:
        db.close()


@tool
def toggle_menu_item(item_name: str):
    """Toggles a menu item between active and inactive. Inactive items won't show on the menu."""
    db = SessionLocal()
    try:
        item = db.query(MenuItem).filter(MenuItem.name == item_name).first()
        if not item:
            return f"Menu item '{item_name}' not found."
        item.is_active = not item.is_active
        db.commit()
        status = "active" if item.is_active else "inactive"
        return f"'{item_name}' is now {status}."
    finally:
        db.close()
