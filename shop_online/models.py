from shop_online import db
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from enum import Enum as PyEnum
from itsdangerous import URLSafeTimedSerializer as Serializer


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    orders = db.relationship('Order', back_populates='user')
    carts_items = db.relationship('Cart', back_populates='user')
    wishlists = db.relationship('Wishlist', back_populates='user', uselist=False)
    reviews = db.relationship('Review', back_populates='user')

    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash the password and set it."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)


class ProductCategory(PyEnum):
    biciclette = "biciclette"
    bici_elettriche = "bici Elettriche"
    accessori = "accessori"
    monopattini = "monopattini"
    offerte = "offerte"

    @classmethod
    def singular(cls, category):
        singular_map = {
            cls.biciclette: "bicicletta",
            cls.bici_elettriche: "bici elettrica",
            cls.accessori: "accessorio",
            cls.monopattini: "monopattino",
            cls.offerte: "offerta",
        }
        return singular_map.get(category, None)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ProductCategory), nullable=False)
    content = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=True, default=None)
    flash_sale = db.Column(db.Boolean, default=False)
    image = db.Column(db.String(280), nullable=False)
    image_source = db.Column(db.String(150), nullable=False, default='predefined')
    rating = db.Column(db.Integer, nullable=True)
    review_count = db.Column(db.Integer, nullable=False, default=0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    date_added = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    attributes = db.relationship('ProductAttribute', back_populates='product')
    reviews = db.relationship('Review', back_populates='product')
    carts_items = db.relationship('Cart', back_populates='product')
    order_products = db.relationship('OrderProduct', back_populates='product')
    wishlist_items = db.relationship('WishlistItem', back_populates='product')

    def __repr__(self):
        return (f"<Product(title={self.title}, description={self.description}, "
                f"price={self.price}, category={self.category}, image_source={self.image_source}, quantity={self.quantity})>")


class ProductAttribute(db.Model):
    __tablename__ = 'product_attributes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    material = db.Column(db.String(100), nullable=True)
    capacity = db.Column(db.Float, nullable=True)

    product = db.relationship('Product', back_populates='attributes')
    carts = db.relationship('Cart', back_populates='product_attribute')

    def __repr__(self):
        return (f"<ProductAttribute(color={self.color}, size={self.size}, material={self.material}, "
                f"capacity={self.capacity})>")


class SearchQuery(db.Model):
    __tablename__ = 'search_queries'
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(100), nullable=False)
    search_type = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<SearchQuery(query={self.query}, search_type={self.search_type})>"


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='reviews')
    product = db.relationship('Product', back_populates='reviews')

    def __repr__(self):
        return f"Review(id={self.id}, rating={self.rating}, comment={self.comment}, product_id={self.product_id}, user_id={self.user_id})"


class OrderStatus(PyEnum):
    pending = "Pending"
    shipped = "Spedito"
    completed = "Completato"
    cancelled = "Cancellato"

    def __str__(self):
        return self.value


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(50), nullable=False, default='Pending')
    payment_id = db.Column(db.String(1000), nullable=False)  # ID di Stripe
    date_ordered = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    shipping_address = db.Column(db.String(200), nullable=False)
    billing_address = db.Column(db.String(200), nullable=False)
    order_products = db.relationship('OrderProduct', back_populates='order')

    user = db.relationship('User', back_populates='orders')

    def __repr__(self):
        return (f"Order(id={self.id}, user_id={self.user_id}, total_price={self.total_price}, "
                f"payment_status={self.payment_status}, payment_id={self.payment_id}, date_ordered={self.date_ordered}, "
                f"shipping_address={self.shipping_address}, billing_address={self.billing_address})")


class OrderProduct(db.Model):
    __tablename__ = 'order_products'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', back_populates='order_products')
    product = db.relationship('Product', back_populates='order_products')

    def __repr__(self):
        return (f"OrderProduct(order_id={self.order_id}, product_id={self.product_id}, "
                f"quantity={self.quantity}, price={self.price}, created_at={self.created_at})")


class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_attribute_id = db.Column(db.Integer, db.ForeignKey('product_attributes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', back_populates='carts_items')
    user = db.relationship('User', back_populates='carts_items')
    product_attribute = db.relationship('ProductAttribute', back_populates='carts')

    def __repr__(self):
        return (
            f"Cart(user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity}, product_attribute_id={self.product_attribute_id}, created_at={self.created_at})")


class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    user = db.relationship('User', back_populates='wishlists')
    items = db.relationship('WishlistItem', back_populates='wishlist')

    def __repr__(self):
        return f"Wishlist(id={self.id}, user_id={self.user_id})"


class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_on = db.Column(db.DateTime, default=db.func.current_timestamp())
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.id'), nullable=False)

    product = db.relationship('Product', back_populates='wishlist_items')
    wishlist = db.relationship('Wishlist', back_populates='items')

    def __repr__(self):
        return f"WishlistItem(wishlist_id={self.wishlist_id}, product_id={self.product_id}, added_on={self.added_on})"


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(120), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    def __repr__(self):
        return f"Payment(id={self.id}, session_id={self.session_id}, amount={self.amount}, currency={self.currency}, status={self.status})"
