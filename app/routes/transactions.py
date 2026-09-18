from datetime import datetime, timezone
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models import db, InventoryTransaction, Product
from app.routes.auth import role_required

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions')
@login_required
def index():
    tx_type = request.args.get('type', '').strip()
    product_id = request.args.get('product_id', type=int)
    search = request.args.get('search', '').strip()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()

    query = InventoryTransaction.query.join(Product)

    if tx_type and tx_type in ['STOCK_IN', 'STOCK_OUT']:
        query = query.filter(InventoryTransaction.transaction_type == tx_type)

    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)

    if search:
        query = query.filter(
            (InventoryTransaction.reference_number.ilike(f'%{search}%')) |
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (InventoryTransaction.notes.ilike(f'%{search}%')) |
            (InventoryTransaction.destination.ilike(f'%{search}%'))
        )

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
    products = Product.query.order_by(Product.name.asc()).all()

    return render_template(
        'transactions/list.html',
        transactions=transactions,
        products=products,
        selected_type=tx_type,
        selected_product_id=product_id,
        search=search,
        from_date=from_date,
        to_date=to_date
    )
