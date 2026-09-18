from datetime import datetime, timezone
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from app.models import Product, db
from app.services.report_service import (
    generate_inventory_report_data,
    generate_inventory_csv,
    generate_stock_movement_report_data,
    generate_movement_csv,
    generate_low_stock_report_data,
    generate_low_stock_csv
)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def index():
    tab = request.args.get('tab', 'inventory').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()
    tx_type = request.args.get('type', '').strip()
    product_id = request.args.get('product_id', type=int)

    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]
    all_products = Product.query.order_by(Product.name.asc()).all()

    # Data for the active tab
    inventory_data, inventory_summary = generate_inventory_report_data(category=category, status=status)
    movement_data, movement_summary = generate_stock_movement_report_data(from_date=from_date, to_date=to_date, tx_type=tx_type, product_id=product_id)
    low_stock_data, low_stock_summary = generate_low_stock_report_data()

    return render_template(
        'reports/index.html',
        active_tab=tab,
        categories=categories,
        all_products=all_products,
        inventory_data=inventory_data,
        inventory_summary=inventory_summary,
        movement_data=movement_data,
        movement_summary=movement_summary,
        low_stock_data=low_stock_data,
        low_stock_summary=low_stock_summary,
        selected_category=category,
        selected_status=status,
        from_date=from_date,
        to_date=to_date,
        selected_type=tx_type,
        selected_product_id=product_id
    )


@reports_bp.route('/reports/inventory/csv')
@login_required
def export_inventory_csv():
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    csv_data = generate_inventory_csv(category=category, status=status)
    filename = f"warehouse_inventory_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/reports/movements/csv')
@login_required
def export_movements_csv():
    from_date = request.args.get('from_date', '').strip()
    to_date = request.args.get('to_date', '').strip()
    tx_type = request.args.get('type', '').strip()
    product_id = request.args.get('product_id', type=int)
    csv_data = generate_movement_csv(from_date=from_date, to_date=to_date, tx_type=tx_type, product_id=product_id)
    filename = f"stock_movements_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/reports/low-stock/csv')
@login_required
def export_low_stock_csv():
    csv_data = generate_low_stock_csv()
    filename = f"low_stock_reorder_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
