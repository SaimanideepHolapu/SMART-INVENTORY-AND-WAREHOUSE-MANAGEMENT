from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.models import db, Product, InventoryTransaction, Supplier
from app.services.inventory_service import get_category_breakdown, get_stock_movement_trends, get_kpis

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    kpis = get_kpis()
    categories = get_category_breakdown()

    # Top 5 most dispatched products (Fastest Moving)
    top_dispatched = db.session.query(
        Product.name,
        Product.sku,
        func.sum(InventoryTransaction.quantity).label('total_out')
    ).join(InventoryTransaction, InventoryTransaction.product_id == Product.id)\
     .filter(InventoryTransaction.transaction_type == 'STOCK_OUT')\
     .group_by(Product.id)\
     .order_by(func.sum(InventoryTransaction.quantity).desc())\
     .limit(5).all()

    # Top 5 intake products
    top_received = db.session.query(
        Product.name,
        Product.sku,
        func.sum(InventoryTransaction.quantity).label('total_in')
    ).join(InventoryTransaction, InventoryTransaction.product_id == Product.id)\
     .filter(InventoryTransaction.transaction_type == 'STOCK_IN')\
     .group_by(Product.id)\
     .order_by(func.sum(InventoryTransaction.quantity).desc())\
     .limit(5).all()

    # Stock health distribution
    in_stock_count = kpis['total_products'] - kpis['low_stock_count'] - kpis['out_of_stock_count']
    stock_health = {
        'in_stock': max(0, in_stock_count),
        'low_stock': kpis['low_stock_count'],
        'out_of_stock': kpis['out_of_stock_count']
    }

    return render_template(
        'analytics/index.html',
        kpis=kpis,
        categories=categories,
        top_dispatched=top_dispatched,
        top_received=top_received,
        stock_health=stock_health
    )

@analytics_bp.route('/api/analytics/charts')
@login_required
def chart_data():
    trends = get_stock_movement_trends(14)
    categories = get_category_breakdown()
    kpis = get_kpis()
    in_stock_count = max(0, kpis['total_products'] - kpis['low_stock_count'] - kpis['out_of_stock_count'])

    return jsonify({
        'trends': trends,
        'categories': categories,
        'health': [in_stock_count, kpis['low_stock_count'], kpis['out_of_stock_count']]
    })
