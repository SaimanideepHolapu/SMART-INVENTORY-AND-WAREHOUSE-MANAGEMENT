from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app.models import db, Product, InventoryTransaction, Supplier, WarehouseLocation

class InsufficientStockError(ValueError):
    """Raised when an inventory dispatch exceeds currently available physical stock."""
    def __init__(self, available, requested):
        self.available = available
        self.requested = requested
        super().__init__(f"Insufficient stock. Available: {available}, Requested: {requested}")


def perform_stock_in(product_id, quantity, supplier_id=None, reference_number=None, notes=None, user_id=None):
    """
    Safely receives inventory into the warehouse.
    Atomic operation: validates inputs, increments stock, creates audit transaction record, and commits.
    """
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Stock In quantity must be a valid whole number.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    product = db.session.get(Product, product_id)
    if not product:
        raise ValueError(f"Product with ID {product_id} not found.")

    if not reference_number or not reference_number.strip():
        # Generate default reference if not provided
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        reference_number = f"IN-{product.sku}-{timestamp}"

    # Increment stock
    product.stock_quantity += quantity
    product.updated_at = datetime.now(timezone.utc)

    # Use product's supplier if none specifically provided in the form
    resolved_supplier_id = supplier_id if supplier_id else product.supplier_id

    # Create transaction
    tx = InventoryTransaction(
        product_id=product.id,
        transaction_type='STOCK_IN',
        quantity=quantity,
        reference_number=reference_number.strip(),
        supplier_id=resolved_supplier_id,
        destination=None,
        performed_by=user_id,
        notes=notes.strip() if notes else None,
        created_at=datetime.now(timezone.utc)
    )

    db.session.add(tx)
    db.session.commit()
    return tx, product


def perform_stock_out(product_id, quantity, destination=None, reference_number=None, notes=None, user_id=None):
    """
    Safely dispatches inventory out of the warehouse.
    Atomic operation: validates inputs, verifies sufficient stock, decrements stock, creates audit transaction, and commits.
    """
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Stock Out quantity must be a valid whole number.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    product = db.session.get(Product, product_id)
    if not product:
        raise ValueError(f"Product with ID {product_id} not found.")

    # Prevent negative stock
    if quantity > product.stock_quantity:
        raise InsufficientStockError(available=product.stock_quantity, requested=quantity)

    if not destination or not destination.strip():
        raise ValueError("Destination is required for Stock Out (e.g., Customer Order, Department, Warehouse).")

    if not reference_number or not reference_number.strip():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        reference_number = f"OUT-{product.sku}-{timestamp}"

    # Decrement stock
    product.stock_quantity -= quantity
    product.updated_at = datetime.now(timezone.utc)

    # Create transaction
    tx = InventoryTransaction(
        product_id=product.id,
        transaction_type='STOCK_OUT',
        quantity=quantity,
        reference_number=reference_number.strip(),
        supplier_id=None,
        destination=destination.strip(),
        performed_by=user_id,
        notes=notes.strip() if notes else None,
        created_at=datetime.now(timezone.utc)
    )

    db.session.add(tx)
    db.session.commit()
    return tx, product


def get_kpis():
    """
    Computes real-time warehouse KPIs directly from database tables.
    """
    total_products = db.session.query(func.count(Product.id)).scalar() or 0
    total_stock_units = db.session.query(func.sum(Product.stock_quantity)).scalar() or 0

    # Low stock: stock > 0 and stock <= min
    low_stock_count = Product.query.filter(
        Product.stock_quantity > 0,
        Product.stock_quantity <= Product.minimum_stock
    ).count()

    # Out of stock: stock <= 0
    out_of_stock_count = Product.query.filter(Product.stock_quantity <= 0).count()

    # Total valuation
    total_valuation = db.session.query(func.sum(Product.stock_quantity * Product.price)).scalar() or 0.0

    # Movements today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    stock_in_today = db.session.query(func.sum(InventoryTransaction.quantity)).filter(
        InventoryTransaction.transaction_type == 'STOCK_IN',
        InventoryTransaction.created_at >= today_start
    ).scalar() or 0

    stock_out_today = db.session.query(func.sum(InventoryTransaction.quantity)).filter(
        InventoryTransaction.transaction_type == 'STOCK_OUT',
        InventoryTransaction.created_at >= today_start
    ).scalar() or 0

    return {
        'total_products': total_products,
        'total_stock_units': total_stock_units,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_valuation': round(total_valuation, 2),
        'stock_in_today': stock_in_today,
        'stock_out_today': stock_out_today,
    }


def get_low_stock_products():
    """
    Returns products requiring urgent reordering (out of stock and low stock).
    """
    return Product.query.filter(Product.stock_quantity <= Product.minimum_stock).order_by(Product.stock_quantity.asc()).all()


def get_recent_transactions(limit=10):
    """
    Returns the latest transactions with relations preloaded.
    """
    return InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()


def get_category_breakdown():
    """
    Returns product count, stock volume, and valuation grouped by category.
    """
    results = db.session.query(
        Product.category,
        func.count(Product.id).label('product_count'),
        func.sum(Product.stock_quantity).label('total_units'),
        func.sum(Product.stock_quantity * Product.price).label('total_value')
    ).group_by(Product.category).all()

    categories = []
    for row in results:
        categories.append({
            'category': row.category,
            'product_count': row.product_count,
            'total_units': int(row.total_units or 0),
            'total_value': round(float(row.total_value or 0.0), 2)
        })
    return categories


def get_stock_movement_trends(days=7):
    """
    Returns daily in/out unit movement arrays for the past N days for Chart.js.
    """
    now = datetime.now(timezone.utc)
    dates = []
    stock_in_series = []
    stock_out_series = []

    for i in range(days - 1, -1, -1):
        target_day = now - timedelta(days=i)
        day_start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = target_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        day_label = target_day.strftime("%b %d")

        in_qty = db.session.query(func.sum(InventoryTransaction.quantity)).filter(
            InventoryTransaction.transaction_type == 'STOCK_IN',
            InventoryTransaction.created_at >= day_start,
            InventoryTransaction.created_at <= day_end
        ).scalar() or 0

        out_qty = db.session.query(func.sum(InventoryTransaction.quantity)).filter(
            InventoryTransaction.transaction_type == 'STOCK_OUT',
            InventoryTransaction.created_at >= day_start,
            InventoryTransaction.created_at <= day_end
        ).scalar() or 0

        dates.append(day_label)
        stock_in_series.append(int(in_qty))
        stock_out_series.append(int(out_qty))

    return {
        'labels': dates,
        'stock_in': stock_in_series,
        'stock_out': stock_out_series
    }
