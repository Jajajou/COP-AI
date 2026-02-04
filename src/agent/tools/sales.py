import logging

from langchain_core.tools import tool
from src.agent.clients.postgres import SessionLocal
from src.agent.domain.models import MenuItem, InventoryItem, Sale, Recipe, Order, OrderItem, InventoryLog

logger = logging.getLogger(__name__)


@tool
def sell_menu_item(item_name: str, quantity: int = 1, payment_method: str = "cash"):
    """Records a sale of a menu item. Auto-deducts ingredients based on recipe (back-flushing).
    Creates an Order record for tracking. Payment methods: cash, card, transfer."""
    if quantity <= 0:
        return "Error: Quantity must be a positive number."
    if payment_method not in ("cash", "card", "transfer"):
        return "Error: Payment method must be 'cash', 'card', or 'transfer'."

    db = SessionLocal()
    try:
        menu_item = db.query(MenuItem).filter(
            MenuItem.name == item_name,
            MenuItem.is_active == True
        ).first()
        if not menu_item:
            return f"Error: '{item_name}' is not on the menu or is inactive."

        recipes = db.query(Recipe).filter(Recipe.product_id == menu_item.id).all()

        # Lock ingredient rows and validate stock atomically
        ingredient_deductions = []
        if recipes:
            for r in recipes:
                ingredient = db.query(InventoryItem).filter(
                    InventoryItem.id == r.ingredient_id
                ).with_for_update().first()
                if not ingredient:
                    return f"Error: Recipe ingredient (ID {r.ingredient_id}) not found in inventory."
                needed = r.amount_needed * quantity
                if ingredient.quantity < needed:
                    return (
                        f"Error: Insufficient '{ingredient.name}'. "
                        f"Need {needed} {ingredient.unit}, have {ingredient.quantity} {ingredient.unit}."
                    )
                ingredient_deductions.append((ingredient, needed))

        total = menu_item.price * quantity

        order = Order(total_amount=total, payment_method=payment_method)
        db.add(order)
        db.flush()

        order_item = OrderItem(
            order_id=order.id,
            product_id=menu_item.id,
            quantity=quantity,
            price_at_sale=menu_item.price
        )
        db.add(order_item)

        deducted_items = []
        for ingredient, deduction in ingredient_deductions:
            ingredient.quantity -= deduction
            log = InventoryLog(
                ingredient_id=ingredient.id,
                change_amount=-deduction,
                reason=f"sale_backflush:order_{order.id}"
            )
            db.add(log)
            deducted_items.append(f"{ingredient.name}: -{deduction} {ingredient.unit}")

        sale = Sale(item_name=item_name, quantity=quantity, total_amount=total, sale_type="MENU")
        db.add(sale)
        db.commit()

        result = f"Sold {quantity}x {item_name} for ${total} (Order #{order.id}, {payment_method})."
        if deducted_items:
            result += "\nIngredients deducted:\n" + "\n".join(f"  - {d}" for d in deducted_items)
        return result
    except Exception as e:
        db.rollback()
        logger.error(f"Error in sell_menu_item: {e}", exc_info=True)
        return "An error occurred while processing the sale. Please try again."
    finally:
        db.close()


@tool
def sell_inventory_item(item_name: str, quantity: float):
    """Sells a raw inventory item by weight/quantity (e.g., selling loose coffee beans).
    Deducts stock and logs the change automatically."""
    if quantity <= 0:
        return "Error: Quantity must be a positive number."

    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(
            InventoryItem.name == item_name
        ).with_for_update().first()
        if not item:
            return f"Error: '{item_name}' not found in inventory."

        if item.quantity < quantity:
            return f"Error: Insufficient stock. Only {item.quantity} {item.unit} available."

        total = item.unit_price * quantity
        item.quantity -= quantity

        log = InventoryLog(
            ingredient_id=item.id,
            change_amount=-quantity,
            reason="direct_inventory_sale"
        )
        db.add(log)

        sale = Sale(item_name=item_name, quantity=quantity, total_amount=total, sale_type="INVENTORY")
        db.add(sale)
        db.commit()
        return (
            f"Sold {quantity} {item.unit} of {item_name} for ${total}. "
            f"Remaining stock: {item.quantity} {item.unit}."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error in sell_inventory_item: {e}", exc_info=True)
        return "An error occurred while processing the sale. Please try again."
    finally:
        db.close()


@tool
def quick_sale(item_description: str, amount: float):
    """Records a quick sale for items NOT in the menu or for loose adjustments.
    Useful for selling random items, custom charges, or correcting cash balances.
    To REFUND or DEDUCT revenue, provide a negative 'amount'.
    """
    db = SessionLocal()
    try:
        # We record this as a 'Sale' with a special type "QUICK"
        # Since it's not a menu item or inventory item, we don't track quantity precisely (use 1)
        # and we don't deduct stock.
        sale = Sale(
            item_name=item_description,
            quantity=1,
            total_amount=amount,
            sale_type="QUICK"
        )
        db.add(sale)
        db.commit()
        
        if amount >= 0:
            return f"Quick sale recorded: '{item_description}' for {amount} VND."
        else:
            return f"Refund/Deduction recorded: '{item_description}' for {amount} VND."
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error in quick_sale: {e}", exc_info=True)
        return "An error occurred while processing the quick sale."
    finally:
        db.close()
