from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Product, Supplier, InventoryTransaction
from app.routes.auth import role_required
from app.services.inventory_service import perform_stock_in, perform_stock_out, InsufficientStockError

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()

    query = Product.query

    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.sku.ilike(f'%{search}%')) |
            (Product.product_code.ilike(f'%{search}%'))
        )

    if category_filter:
        query = query.filter(Product.category == category_filter)

    products = query.order_by(Product.name.asc()).all()

    if status_filter:
        products = [p for p in products if p.status == status_filter]

    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    return render_template(
        'inventory/index.html',
        products=products,
        categories=categories,
        selected_status=status_filter,
        selected_category=category_filter,
        search=search
    )


@inventory_bp.route('/inventory/stock-in', methods=['GET', 'POST'])
@role_required('ADMIN', 'STAFF')
def stock_in():
    products = Product.query.order_by(Product.name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    selected_product_id = request.args.get('product_id', type=int)

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity')
        supplier_id = request.form.get('supplier_id', type=int) or None
        reference_number = request.form.get('reference_number', '').strip()
        notes = request.form.get('notes', '').strip()

        if not product_id:
            flash("Please select a product.", "danger")
            return render_template('inventory/stock_in.html', products=products, suppliers=suppliers, selected_product_id=selected_product_id)

        try:
            tx, product = perform_stock_in(
                product_id=product_id,
                quantity=quantity,
                supplier_id=supplier_id,
                reference_number=reference_number,
                notes=notes,
                user_id=current_user.id
            )
            flash(f"Successfully received +{tx.quantity} units of '{product.name}' (SKU: {product.sku})! New stock: {product.stock_quantity} units.", "success")
            return redirect(url_for('products.detail', id=product.id))
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"An error occurred during Stock In: {str(e)}", "danger")

    return render_template('inventory/stock_in.html', products=products, suppliers=suppliers, selected_product_id=selected_product_id)


@inventory_bp.route('/inventory/stock-out', methods=['GET', 'POST'])
@role_required('ADMIN', 'STAFF')
def stock_out():
    products = Product.query.order_by(Product.name.asc()).all()
    selected_product_id = request.args.get('product_id', type=int)

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity')
        destination = request.form.get('destination', '').strip()
        reference_number = request.form.get('reference_number', '').strip()
        notes = request.form.get('notes', '').strip()

        if not product_id:
            flash("Please select a product.", "danger")
            return render_template('inventory/stock_out.html', products=products, selected_product_id=selected_product_id)

        try:
            tx, product = perform_stock_out(
                product_id=product_id,
                quantity=quantity,
                destination=destination,
                reference_number=reference_number,
                notes=notes,
                user_id=current_user.id
            )
            flash(f"Successfully dispatched -{tx.quantity} units of '{product.name}' (SKU: {product.sku}) to '{destination}'! New stock: {product.stock_quantity} units.", "success")
            return redirect(url_for('products.detail', id=product.id))
        except InsufficientStockError as ise:
            flash(f"Insufficient stock: Available: {ise.available}, Requested: {ise.requested}.", "danger")
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"An error occurred during Stock Out: {str(e)}", "danger")

    return render_template('inventory/stock_out.html', products=products, selected_product_id=selected_product_id)
