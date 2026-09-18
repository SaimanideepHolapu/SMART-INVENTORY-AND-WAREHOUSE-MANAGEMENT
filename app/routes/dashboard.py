from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.services.inventory_service import (
    get_kpis,
    get_low_stock_products,
    get_recent_transactions,
    get_category_breakdown,
    get_stock_movement_trends
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    kpis = get_kpis()
    low_stock_items = get_low_stock_products()
    recent_transactions = get_recent_transactions(8)
    categories = get_category_breakdown()
    return render_template(
        'dashboard/index.html',
        kpis=kpis,
        low_stock_items=low_stock_items,
        recent_transactions=recent_transactions,
        categories=categories
    )

@dashboard_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    trends = get_stock_movement_trends(7)
    categories = get_category_breakdown()

    category_labels = [c['category'] for c in categories]
    category_units = [c['total_units'] for c in categories]
    category_values = [c['total_value'] for c in categories]

    return jsonify({
        'trends': trends,
        'categories': {
            'labels': category_labels,
            'units': category_units,
            'values': category_values
        }
    })

@dashboard_bp.route('/api/notifications')
@login_required
def notifications():
    low_stock = get_low_stock_products()
    alerts = []
    for p in low_stock:
        alerts.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'stock': p.stock_quantity,
            'min': p.minimum_stock,
            'status': p.status,
            'is_critical': p.stock_quantity == 0
        })

    return jsonify({
        'count': len(alerts),
        'alerts': alerts
    })
