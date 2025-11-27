"""
Database models for the bot's own PostgreSQL database
"""
from datetime import datetime
from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, Numeric, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Telegram user model"""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    opencart_customer_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id} ({self.first_name})>"


class Cart(Base):
    """Shopping cart items"""
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, nullable=False, index=True)  # OpenCart product_id
    quantity = Column(Integer, default=1)
    options = Column(JSON, nullable=True)  # Product options (if any)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="carts")

    def __repr__(self):
        return f"<Cart user={self.user_id} product={self.product_id} qty={self.quantity}>"


class Order(Base):
    """Orders created through the bot"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    opencart_order_id = Column(Integer, nullable=True, index=True)
    yoomoney_payment_id = Column(String(255), nullable=True)
    yoomoney_label = Column(String(255), nullable=True, unique=True)

    # Order details
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="pending")  # pending, paid, cancelled, refunded, completed

    # Customer information
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_email = Column(String(255), nullable=True)

    # Delivery information
    delivery_address = Column(Text, nullable=True)
    delivery_comment = Column(Text, nullable=True)

    # Order items (JSON)
    items = Column(JSON, nullable=False)  # List of {product_id, name, price, quantity}

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")

    def __repr__(self):
        return f"<Order {self.id} user={self.user_id} amount={self.amount} status={self.status}>"


class SupportTicket(Base):
    """Support tickets from users"""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    admin_response = Column(Text, nullable=True)
    status = Column(String(20), default="open")  # open, answered, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="support_tickets")

    def __repr__(self):
        return f"<SupportTicket {self.id} user={self.user_id} status={self.status}>"
