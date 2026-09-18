from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default='STAFF'
    )  # ADMIN, STAFF, MANAGER
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # QR code for user
    qr_code = db.Column(db.String(255), unique=True)

    transactions = db.relationship(
        'InventoryTransaction',
        backref='performer',
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_staff(self):
        return self.role == 'STAFF'

    @property
    def is_manager(self):
        return self.role == 'MANAGER'

    @property
    def is_active(self):
        return self.is_active_user

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    products = db.relationship(
        'Product',
        backref='supplier',
        lazy=True
    )

    transactions = db.relationship(
        'InventoryTransaction',
        backref='supplier',
        lazy=True
    )

    @property
    def total_products_count(self):
        return len(self.products)

    @property
    def total_units_in_stock(self):
        return sum(p.stock_quantity for p in self.products)

    def __repr__(self):
        return f'<Supplier {self.supplier_code}: {self.name}>'


class WarehouseLocation(db.Model):
    __tablename__ = 'warehouse_locations'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(20), nullable=False)
    aisle = db.Column(db.String(20), nullable=False)
    rack = db.Column(db.String(20), nullable=False)
    shelf = db.Column(db.String(20), nullable=False)

    products = db.relationship(
        'Product',
        backref='location',
        lazy=True
    )

    @property
    def full_location(self):
        return (
            f"{self.warehouse_name} > "
            f"Zone {self.zone} > "
            f"Aisle {self.aisle} > "
            f"Rack {self.rack} > "
            f"Shelf {self.shelf}"
        )

    @property
    def short_code(self):
        # Example: WH-A-ZA-A01-R02-S01
        wh_short = self.warehouse_name.replace(
            "Warehouse ",
            "WH-"
        )

        return (
            f"{wh_short}-"
            f"Z{self.zone}-"
            f"A{self.aisle}-"
            f"R{self.rack}-"
            f"S{self.shelf}"
        )

    def __repr__(self):
        return f'<Location {self.short_code}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    # Product identification
    product_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    sku = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # Product information
    name = db.Column(
        db.String(150),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    # Pricing and inventory
    price = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    stock_quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    minimum_stock = db.Column(
        db.Integer,
        nullable=False,
        default=10
    )

    # Warehouse location
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('warehouse_locations.id'),
        nullable=True
    )

    # Supplier
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('suppliers.id'),
        nullable=True
    )

    # Product image
    image_filename = db.Column(
        db.String(255),
        nullable=True
    )

    # Product QR code
    qr_code = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Inventory transactions
    transactions = db.relationship(
        'InventoryTransaction',
        backref='product',
        lazy='dynamic',
        cascade="all, delete-orphan"
    )

    @property
    def image_url(self):
        if self.image_filename:
            return f"/static/uploads/products/{self.image_filename}"

        return None

    @property
    def qr_image_url(self):
        return f"/static/qrcodes/{self.sku}.png"

    @property
    def status(self):
        """
        Dynamically computed stock status:

        stock_quantity == 0
            -> OUT OF STOCK

        stock_quantity <= minimum_stock
            -> LOW STOCK

        stock_quantity > minimum_stock
            -> IN STOCK
        """

        if self.stock_quantity <= 0:
            return 'OUT OF STOCK'

        elif self.stock_quantity <= self.minimum_stock:
            return 'LOW STOCK'

        else:
            return 'IN STOCK'

    @property
    def status_badge_class(self):
        s = self.status

        if s == 'OUT OF STOCK':
            return 'badge-out-of-stock'

        elif s == 'LOW STOCK':
            return 'badge-low-stock'

        return 'badge-in-stock'

    @property
    def is_low_stock(self):
        return (
            0 < self.stock_quantity <= self.minimum_stock
        )

    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    @property
    def total_value(self):
        return round(
            self.stock_quantity * (self.price or 0.0),
            2
        )

    def to_dict(self):
        return {
            'id': self.id,
            'product_code': self.product_code,
            'sku': self.sku,
            'name': self.name,
            'category': self.category,
            'description': self.description or '',
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'minimum_stock': self.minimum_stock,

            'status': self.status,
            'status_badge_class': self.status_badge_class,

            'location': (
                self.location.short_code
                if self.location
                else 'Unassigned'
            ),

            'location_full': (
                self.location.full_location
                if self.location
                else 'Unassigned'
            ),

            'supplier': (
                self.supplier.name
                if self.supplier
                else 'None'
            ),

            'supplier_code': (
                self.supplier.supplier_code
                if self.supplier
                else 'None'
            ),

            'qr_code': self.qr_code or self.sku,

            'image_url': self.image_url,

            'qr_image_url': self.qr_image_url
        }

    def __repr__(self):
        return (
            f'<Product {self.sku}: '
            f'{self.name} '
            f'({self.stock_quantity} units)>'
        )


class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('products.id'),
        nullable=False,
        index=True
    )

    transaction_type = db.Column(
        db.String(20),
        nullable=False,
        index=True
    )  # STOCK_IN, STOCK_OUT

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    reference_number = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey('suppliers.id'),
        nullable=True
    )

    destination = db.Column(
        db.String(150),
        nullable=True
    )  # For STOCK_OUT

    performed_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    @property
    def quantity_formatted(self):
        if self.transaction_type == 'STOCK_IN':
            return f"+{self.quantity}"

        return f"-{self.quantity}"

    @property
    def type_badge_class(self):
        if self.transaction_type == 'STOCK_IN':
            return 'badge-stock-in'

        return 'badge-stock-out'

    def __repr__(self):
        return (
            f'<Transaction {self.reference_number}: '
            f'{self.transaction_type} '
            f'{self.quantity} '
            f'of Product {self.product_id}>'
        )