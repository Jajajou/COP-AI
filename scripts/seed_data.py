import sys
import os

# Add the project root to the python path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.clients.postgres import SessionLocal, init_db
from src.agent.domain.models import InventoryItem, MenuItem, Recipe

def get_db_session():
    return SessionLocal()

def import_stock(session, name, quantity, unit):
    item = session.query(InventoryItem).filter(InventoryItem.name == name).first()
    if item:
        print(f"Updating Stock: {name} ({quantity} {unit})")
        item.quantity = quantity
        item.unit = unit
    else:
        print(f"Creating Stock: {name} ({quantity} {unit})")
        item = InventoryItem(name=name, quantity=quantity, unit=unit)
        session.add(item)
    session.commit()

def add_product(session, name, price, category):
    item = session.query(MenuItem).filter(MenuItem.name == name).first()
    if item:
        print(f"Updating Product: {name} - {price} VND")
        item.price = price
        item.category = category
    else:
        print(f"Creating Product: {name} - {price} VND")
        item = MenuItem(name=name, price=price, category=category)
        session.add(item)
    session.commit()

def add_recipe(session, product_name, ingredient_name, amount):
    product = session.query(MenuItem).filter(MenuItem.name == product_name).first()
    ingredient = session.query(InventoryItem).filter(InventoryItem.name == ingredient_name).first()

    if not product:
        print(f"Error: Product '{product_name}' not found.")
        return
    if not ingredient:
        print(f"Error: Ingredient '{ingredient_name}' not found.")
        return

    # Check if recipe exists
    recipe = session.query(Recipe).filter(
        Recipe.product_id == product.id,
        Recipe.ingredient_id == ingredient.id
    ).first()

    if recipe:
        print(f"Updating Recipe: {product_name} needs {amount} of {ingredient_name}")
        recipe.amount_needed = amount
    else:
        print(f"Creating Recipe: {product_name} needs {amount} of {ingredient_name}")
        recipe = Recipe(product_id=product.id, ingredient_id=ingredient.id, amount_needed=amount)
        session.add(recipe)
    session.commit()

def seed():
    print("Initializing Database...")
    init_db() # Ensure tables exist
    
    session = get_db_session()
    try:
        # --- PHẦN 1: KHỞI TẠO NGUYÊN LIỆU ---
        print("\n--- SEEDING INVENTORY ---")
        import_stock(session, 'Hạt Cafe', 1000, 'g')
        import_stock(session, 'Sữa đặc', 10, 'lit')
        import_stock(session, 'Sữa tươi', 10, 'lit')
        import_stock(session, 'Sữa Yến Mạch (Oat)', 5, 'lit')
        import_stock(session, 'Bột Matcha', 500, 'g')
        import_stock(session, 'Bột Cacao', 500, 'g')
        import_stock(session, 'Đường nước', 5, 'lit')
        # Handmade
        import_stock(session, 'Cốt Tepache', 0, 'ml')
        import_stock(session, 'Cốt Kefir Nước', 0, 'ml')
        import_stock(session, 'Cốt Kefir Sữa', 0, 'ml')
        import_stock(session, 'Nước Mơ ngâm', 0, 'ml')
        import_stock(session, 'Nước Cam', 0, 'ml') # Added based on usage in Orange Espresso
        import_stock(session, 'Syrup Quế', 0, 'ml') # Added based on usage
        import_stock(session, 'Đậu đỏ sên', 0, 'g') # Added based on usage
        import_stock(session, 'Nước cốt dừa', 0, 'ml') # Added based on usage
        import_stock(session, 'Syrup Gừng', 0, 'ml') # Added based on usage
        import_stock(session, 'Mứt Trái Cây', 0, 'g') # Added based on usage
        import_stock(session, 'Nước Mía', 0, 'ml') # Added based on usage
        import_stock(session, 'Mứt Dâu', 0, 'g') # Added based on usage
        import_stock(session, 'Chuối tươi', 0, 'g') # Added based on usage

        # --- PHẦN 2: MENU & CÔNG THỨC ---
        print("\n--- SEEDING MENU & RECIPES ---")

        # 1. CAFE TRUYỀN THỐNG
        add_product(session, 'Cafe Đen', 22000, 'Cafe')
        add_recipe(session, 'Cafe Đen', 'Hạt Cafe', 18)
        add_recipe(session, 'Cafe Đen', 'Đường nước', 10)

        add_product(session, 'Cafe Sữa', 25000, 'Cafe')
        add_recipe(session, 'Cafe Sữa', 'Hạt Cafe', 18)
        add_recipe(session, 'Cafe Sữa', 'Sữa đặc', 30)

        add_product(session, 'Bạc Xỉu', 30000, 'Cafe')
        add_recipe(session, 'Bạc Xỉu', 'Hạt Cafe', 10)
        add_recipe(session, 'Bạc Xỉu', 'Sữa đặc', 30)
        add_recipe(session, 'Bạc Xỉu', 'Sữa tươi', 60)

        add_product(session, 'Espresso', 30000, 'Cafe')
        add_recipe(session, 'Espresso', 'Hạt Cafe', 18)

        add_product(session, 'Americano', 30000, 'Cafe')
        add_recipe(session, 'Americano', 'Hạt Cafe', 18)

        # 2. BEST SELLER (LATTE)
        add_product(session, 'Latte Fresh Milk', 40000, 'Latte')
        add_recipe(session, 'Latte Fresh Milk', 'Hạt Cafe', 18)
        add_recipe(session, 'Latte Fresh Milk', 'Sữa tươi', 150)

        add_product(session, 'Latte Oat Side', 40000, 'Latte')
        add_recipe(session, 'Latte Oat Side', 'Hạt Cafe', 18)
        add_recipe(session, 'Latte Oat Side', 'Sữa Yến Mạch (Oat)', 150)

        # 3. MATCHA SERIES
        add_product(session, 'Matcha Latte', 40000, 'Matcha')
        add_recipe(session, 'Matcha Latte', 'Bột Matcha', 5)
        add_recipe(session, 'Matcha Latte', 'Sữa tươi', 150)

        add_product(session, 'Matcha Đậu đỏ', 40000, 'Matcha')
        add_recipe(session, 'Matcha Đậu đỏ', 'Bột Matcha', 5)
        add_recipe(session, 'Matcha Đậu đỏ', 'Sữa tươi', 120)
        add_recipe(session, 'Matcha Đậu đỏ', 'Đậu đỏ sên', 30)

        add_product(session, 'Matcha Dừa', 37000, 'Matcha')
        add_recipe(session, 'Matcha Dừa', 'Bột Matcha', 5)
        add_recipe(session, 'Matcha Dừa', 'Nước cốt dừa', 50)

        # 4. CAFE MIX (SIGNATURE)
        add_product(session, 'Orange Espresso', 37000, 'Signature')
        add_recipe(session, 'Orange Espresso', 'Hạt Cafe', 18)
        add_recipe(session, 'Orange Espresso', 'Nước Cam', 60)
        add_recipe(session, 'Orange Espresso', 'Syrup Quế', 10)

        add_product(session, 'Coco Espresso', 37000, 'Signature')
        add_recipe(session, 'Coco Espresso', 'Hạt Cafe', 18)
        add_recipe(session, 'Coco Espresso', 'Nước cốt dừa', 60)

        add_product(session, 'Black Dream Summer', 37000, 'Signature')
        add_recipe(session, 'Black Dream Summer', 'Hạt Cafe', 18)
        add_recipe(session, 'Black Dream Summer', 'Nước Mơ ngâm', 40)

        # 5. KEFIR NƯỚC & MÍA
        add_product(session, 'Kefir Nước Nguyên Vị', 27000, 'Lên men')
        add_recipe(session, 'Kefir Nước Nguyên Vị', 'Cốt Kefir Nước', 200)

        add_product(session, 'Kefir Gừng Quế', 30000, 'Lên men')
        add_recipe(session, 'Kefir Gừng Quế', 'Cốt Kefir Nước', 180)
        add_recipe(session, 'Kefir Gừng Quế', 'Syrup Gừng', 10)

        add_product(session, 'Kefir Trái Cây', 30000, 'Lên men')
        add_recipe(session, 'Kefir Trái Cây', 'Cốt Kefir Nước', 150)
        add_recipe(session, 'Kefir Trái Cây', 'Mứt Trái Cây', 30)

        add_product(session, 'Kefir Mía Nguyên Vị', 27000, 'Lên men')
        add_recipe(session, 'Kefir Mía Nguyên Vị', 'Nước Mía', 150)
        add_recipe(session, 'Kefir Mía Nguyên Vị', 'Cốt Kefir Nước', 50)

        # 6. TEPACHE
        add_product(session, 'Tepache Có Gas', 30000, 'Lên men')
        add_recipe(session, 'Tepache Có Gas', 'Cốt Tepache', 200)

        add_product(session, 'Tepache Không Gas', 30000, 'Lên men')
        add_recipe(session, 'Tepache Không Gas', 'Cốt Tepache', 200)

        # 7. KEFIR SỮA
        add_product(session, 'Kefir Sữa Nguyên Vị', 30000, 'Lên men')
        add_recipe(session, 'Kefir Sữa Nguyên Vị', 'Cốt Kefir Sữa', 250)

        add_product(session, 'Kefir Sữa Mứt Dâu', 35000, 'Lên men')
        add_recipe(session, 'Kefir Sữa Mứt Dâu', 'Cốt Kefir Sữa', 200)
        add_recipe(session, 'Kefir Sữa Mứt Dâu', 'Mứt Dâu', 30)

        # 8. DAILY DRINK
        add_product(session, 'Nước Mơ', 30000, 'Daily')
        add_recipe(session, 'Nước Mơ', 'Nước Mơ ngâm', 40)

        add_product(session, 'Cacao Đá', 35000, 'Daily')
        add_recipe(session, 'Cacao Đá', 'Bột Cacao', 10)
        add_recipe(session, 'Cacao Đá', 'Sữa đặc', 30)

        add_product(session, 'Cacao Chuối', 40000, 'Daily')
        add_recipe(session, 'Cacao Chuối', 'Bột Cacao', 10)
        add_recipe(session, 'Cacao Chuối', 'Chuối tươi', 50)
        
        print("Seeding Complete!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed()
