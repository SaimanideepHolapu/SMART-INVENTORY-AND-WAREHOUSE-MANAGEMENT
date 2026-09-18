import io
import csv
from datetime import datetime, timezone
from app.models import Product, InventoryTransaction, Supplier, WarehouseLocation

def generate_inventory_report_data(category=None, status=None):
    """
    Returns filtered product records with computed valuation and status.
    """
    query = Product.query

    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.name.asc()).all()

    # Filter by computed status if requested
    if status:
        if status == 'LOW STOCK':
            products = [p for p in products if p.status == 'LOW STOCK']
        elif status == 'OUT OF STOCK':
            products = [p for p in products if p.status == 'OUT OF STOCK']
        elif status == 'IN STOCK':
            products = [p for p in products if p.status == 'IN STOCK']

    data = []
    total_units = 0
    total_valuation = 0.0

    for p in products:
        val = p.total_value
        total_units += p.stock_quantity
        total_valuation += val
        data.append({
            'product_name': p.name,
            'sku': p.sku,
            'category': p.category,
            'stock_quantity': p.stock_quantity,
            'minimum_stock': p.minimum_stock,
            'status': p.status,
            'price': p.price,
            'total_value': val,
            'location': p.location.short_code if p.location else 'Unassigned',
            'supplier': p.supplier.name if p.supplier else 'None'
        })

    summary = {
        'total_items': len(data),
        'total_units': total_units,
        'total_valuation': round(total_valuation, 2)
    }
    return data, summary


def generate_inventory_csv(category=None, status=None):
    """
    Generates a downloadable CSV string for the current inventory report.
    """
    data, _ = generate_inventory_report_data(category=category, status=status)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Product Name', 'SKU', 'Category', 'Current Stock', 'Minimum Stock',
        'Status', 'Unit Price ($)', 'Total Value ($)', 'Location', 'Supplier'
    ])

    for row in data:
        writer.writerow([
            row['product_name'],
            row['sku'],
            row['category'],
            row['stock_quantity'],
            row['minimum_stock'],
            row['status'],
            f"{row['price']:.2f}",
            f"{row['total_value']:.2f}",
            row['location'],
            row['supplier']
        ])

    return output.getvalue()


def generate_stock_movement_report_data(from_date=None, to_date=None, tx_type=None, product_id=None):
    """
    Returns filtered inventory movement records with audit information.
    """
    query = InventoryTransaction.query

    if tx_type and tx_type in ['STOCK_IN', 'STOCK_OUT']:
        query = query.filter(InventoryTransaction.transaction_type == tx_type)

    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)

    if from_date:
        try:
            dt_from = datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            query = query.filter(InventoryTransaction.created_at >= dt_from)
        except ValueError:
            pass

    if to_date:
        try:
            dt_to = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            query = query.filter(InventoryTransaction.created_at <= dt_to)
        except ValueError:
            pass

    transactions = query.order_by(InventoryTransaction.created_at.desc()).all()

    total_in_units = 0
    total_out_units = 0
    records = []

    for tx in transactions:
        if tx.transaction_type == 'STOCK_IN':
            total_in_units += tx.quantity
            counterpart = tx.supplier.name if tx.supplier else 'Direct Supplier'
        else:
            total_out_units += tx.quantity
            counterpart = tx.destination or 'Customer Dispatch'

        records.append({
            'id': tx.id,
            'date': tx.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'type': tx.transaction_type,
            'product_name': tx.product.name if tx.product else 'Deleted',
            'sku': tx.product.sku if tx.product else 'N/A',
            'quantity': tx.quantity,
            'quantity_display': tx.quantity_formatted,
            'reference_number': tx.reference_number,
            'counterpart': counterpart,
            'performed_by': tx.performer.name if tx.performer else 'System',
            'notes': tx.notes or ''
        })

    summary = {
        'total_movements': len(records),
        'total_in_units': total_in_units,
        'total_out_units': total_out_units,
        'net_change': total_in_units - total_out_units
    }

    return records, summary


def generate_movement_csv(from_date=None, to_date=None, tx_type=None, product_id=None):
    """
    Generates a downloadable CSV string for the stock movement report.
    """
    records, _ = generate_stock_movement_report_data(from_date, to_date, tx_type, product_id)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Transaction ID', 'Date & Time', 'Type', 'Product Name', 'SKU',
        'Quantity', 'Reference Number', 'Counterpart (Supplier/Destination)', 'User', 'Notes'
    ])

    for row in records:
        writer.writerow([
            row['id'],
            row['date'],
            row['type'],
            row['product_name'],
            row['sku'],
            row['quantity_display'],
            row['reference_number'],
            row['counterpart'],
            row['performed_by'],
            row['notes']
        ])

    return output.getvalue()


def generate_low_stock_report_data():
    """
    Returns products requiring urgent reorder action.
    """
    products = Product.query.filter(Product.stock_quantity <= Product.minimum_stock).order_by(Product.stock_quantity.asc()).all()

    records = []
    total_reorder_cost = 0.0

    for p in products:
        deficit = max(0, p.minimum_stock - p.stock_quantity + 10) # recommended reorder buffer
        reorder_cost = deficit * p.price
        total_reorder_cost += reorder_cost

        records.append({
            'product_name': p.name,
            'sku': p.sku,
            'category': p.category,
            'stock_quantity': p.stock_quantity,
            'minimum_stock': p.minimum_stock,
            'status': p.status,
            'suggested_reorder': deficit,
            'unit_price': p.price,
            'reorder_cost': round(reorder_cost, 2),
            'supplier_name': p.supplier.name if p.supplier else 'None',
            'supplier_phone': p.supplier.phone if p.supplier else 'N/A',
            'supplier_email': p.supplier.email if p.supplier else 'N/A',
            'location': p.location.short_code if p.location else 'Unassigned'
        })

    summary = {
        'total_low_stock_items': len(records),
        'total_estimated_reorder_cost': round(total_reorder_cost, 2)
    }
    return records, summary


def generate_low_stock_csv():
    """
    Generates a downloadable CSV string for the low-stock reorder report.
    """
    records, _ = generate_low_stock_report_data()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Product Name', 'SKU', 'Category', 'Current Stock', 'Min Threshold',
        'Status', 'Suggested Reorder Qty', 'Unit Price ($)', 'Est. Reorder Cost ($)',
        'Supplier', 'Supplier Phone', 'Supplier Email', 'Location'
    ])

    for row in records:
        writer.writerow([
            row['product_name'],
            row['sku'],
            row['category'],
            row['stock_quantity'],
            row['minimum_stock'],
            row['status'],
            row['suggested_reorder'],
            f"{row['unit_price']:.2f}",
            f"{row['reorder_cost']:.2f}",
            row['supplier_name'],
            row['supplier_phone'],
            row['supplier_email'],
            row['location']
        ])

    return output.getvalue()
