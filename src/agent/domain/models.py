from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    quantity = Column(Float, default=0.0)
    unit = Column(String, default="kg")
    unit_price = Column(Float, default=0.0)
    min_alert = Column(Float, default=0.0)

    recipes = relationship("Recipe", back_populates="ingredient", cascade="all, delete-orphan")
    logs = relationship("InventoryLog", back_populates="ingredient", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = 'menu_items'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String, default="General")
    is_active = Column(Boolean, default=True)

    recipes = relationship("Recipe", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")


class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    ingredient_id = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    amount_needed = Column(Float, nullable=False)

    product = relationship("MenuItem", back_populates="recipes")
    ingredient = relationship("InventoryItem", back_populates="recipes")


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    payment_method = Column(String, default="cash")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('menu_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_at_sale = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("MenuItem", back_populates="order_items")


class InventoryLog(Base):
    __tablename__ = 'inventory_logs'

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    change_amount = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ingredient = relationship("InventoryItem", back_populates="logs")


class Sale(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    item_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    sale_type = Column(String, nullable=False)
