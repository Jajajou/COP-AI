from langchain_core.tools import tool
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import Recipe, MenuItem, InventoryItem


@tool
def add_recipe(product_name: str, ingredient_name: str, amount_needed: float):
    """Adds an ingredient to a menu item's recipe. E.g., add_recipe('Latte', 'Coffee Beans', 0.02)
    means 1 Latte requires 0.02 kg of Coffee Beans. Updates amount if mapping already exists."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Lỗi: Không tìm thấy món '{product_name}' trong menu."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Lỗi: Không tìm thấy nguyên liệu '{ingredient_name}' trong kho."
        existing = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if existing:
            existing.amount_needed = amount_needed
            db.commit()
            return f"Đã cập nhật công thức: {product_name} hiện dùng {amount_needed} {ingredient.unit} {ingredient_name}."
        recipe = Recipe(product_id=product.id, ingredient_id=ingredient.id, amount_needed=amount_needed)
        db.add(recipe)
        db.commit()
        return f"Đã thêm công thức: {product_name} sử dụng {amount_needed} {ingredient.unit} {ingredient_name}."
    finally:
        db.close()


@tool
def get_recipe(product_name: str):
    """Gets the full recipe (ingredient list) for a menu item."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Không tìm thấy món '{product_name}' trong menu."
        recipes = db.query(Recipe).filter(Recipe.product_id == product.id).all()
        if not recipes:
            return f"Chưa có công thức cho món '{product_name}'."
        lines = [f"Công thức cho món {product_name}:"]
        for r in recipes:
            ingredient = db.query(InventoryItem).filter(InventoryItem.id == r.ingredient_id).first()
            if ingredient:
                lines.append(f"  - {ingredient.name}: {r.amount_needed} {ingredient.unit}")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def update_recipe(product_name: str, ingredient_name: str, new_amount: float):
    """Updates the amount of an ingredient needed for a menu item's recipe."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Không tìm thấy món '{product_name}' trong menu."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Không tìm thấy nguyên liệu '{ingredient_name}' trong kho."
        recipe = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if not recipe:
            return f"Món '{product_name}' chưa có nguyên liệu '{ingredient_name}' trong công thức."
        recipe.amount_needed = new_amount
        db.commit()
        return f"Đã cập nhật: {product_name} hiện dùng {new_amount} {ingredient.unit} {ingredient_name}."
    finally:
        db.close()


@tool
def delete_recipe(product_name: str, ingredient_name: str):
    """Removes an ingredient from a menu item's recipe."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Không tìm thấy món '{product_name}' trong menu."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Không tìm thấy nguyên liệu '{ingredient_name}' trong kho."
        recipe = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if not recipe:
            return f"Không tìm thấy dữ liệu công thức."
        db.delete(recipe)
        db.commit()
        return f"Đã xóa {ingredient_name} khỏi công thức món {product_name}."
    finally:
        db.close()
