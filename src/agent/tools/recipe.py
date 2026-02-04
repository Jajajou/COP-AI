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
            return f"Error: Menu item '{product_name}' not found."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Error: Inventory item '{ingredient_name}' not found."
        existing = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if existing:
            existing.amount_needed = amount_needed
            db.commit()
            return f"Updated recipe: {product_name} now uses {amount_needed} {ingredient.unit} of {ingredient_name}."
        recipe = Recipe(product_id=product.id, ingredient_id=ingredient.id, amount_needed=amount_needed)
        db.add(recipe)
        db.commit()
        return f"Recipe added: {product_name} uses {amount_needed} {ingredient.unit} of {ingredient_name}."
    finally:
        db.close()


@tool
def get_recipe(product_name: str):
    """Gets the full recipe (ingredient list) for a menu item."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Menu item '{product_name}' not found."
        recipes = db.query(Recipe).filter(Recipe.product_id == product.id).all()
        if not recipes:
            return f"No recipe defined for '{product_name}'."
        lines = [f"Recipe for {product_name}:"]
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
            return f"Menu item '{product_name}' not found."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Inventory item '{ingredient_name}' not found."
        recipe = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if not recipe:
            return f"No recipe entry for '{ingredient_name}' in '{product_name}'."
        recipe.amount_needed = new_amount
        db.commit()
        return f"Updated: {product_name} now uses {new_amount} {ingredient.unit} of {ingredient_name}."
    finally:
        db.close()


@tool
def delete_recipe(product_name: str, ingredient_name: str):
    """Removes an ingredient from a menu item's recipe."""
    db = SessionLocal()
    try:
        product = db.query(MenuItem).filter(MenuItem.name == product_name).first()
        if not product:
            return f"Menu item '{product_name}' not found."
        ingredient = db.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()
        if not ingredient:
            return f"Inventory item '{ingredient_name}' not found."
        recipe = db.query(Recipe).filter(
            Recipe.product_id == product.id,
            Recipe.ingredient_id == ingredient.id
        ).first()
        if not recipe:
            return f"No recipe entry found."
        db.delete(recipe)
        db.commit()
        return f"Removed {ingredient_name} from {product_name}'s recipe."
    finally:
        db.close()
