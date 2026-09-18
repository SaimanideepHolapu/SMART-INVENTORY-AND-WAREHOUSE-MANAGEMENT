import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app.models import db, Product, Supplier, WarehouseLocation, InventoryTransaction
from app.routes.auth import role_required
from app.services.qr_service import generate_qr_base64, save_qr_image

products_bp = Blueprint('products', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@products_bp.route('/products')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()

    query = Product.query

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.product_code.ilike(f'%{search}%')
            )
        )

    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.name.asc()).all()

    # Filter by dynamic status if selected
    if status:
        products = [p for p in products if p.status == status]

    # Distinct categories for filter dropdown
    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    return render_template(
        'products/list.html',
        products=products,
        categories=categories,
        search=search,
        selected_category=category,
        selected_status=status
    )


@products_bp.route('/products/new', methods=['GET', 'POST'])
@role_required('ADMIN')
def create():
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    locations = WarehouseLocation.query.order_by(WarehouseLocation.warehouse_name, WarehouseLocation.zone).all()
    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    if request.method == 'POST':
        product_code = request.form.get('product_code', '').strip().upper()
        sku = request.form.get('sku', '').strip().upper()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        new_category = request.form.get('new_category', '').strip()
        if new_category:
            category = new_category

        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0.0')
        initial_stock = request.form.get('stock_quantity', '0')
        minimum_stock = request.form.get('minimum_stock', '10')
        supplier_id = request.form.get('supplier_id') or None
        location_id = request.form.get('location_id') or None

        errors = []
        if not product_code:
            errors.append("Product code is required.")
        if not sku:
            errors.append("SKU is required.")
        if not name:
            errors.append("Product name is required.")
        if not category:
            errors.append("Category is required.")

        try:
            price_val = float(price)
            if price_val < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a valid number.")

        try:
            stock_val = int(initial_stock)
            if stock_val < 0:
                errors.append("Initial stock quantity cannot be negative.")
        except ValueError:
            errors.append("Stock quantity must be a whole number.")

        try:
            min_val = int(minimum_stock)
            if min_val < 0:
                errors.append("Minimum stock cannot be negative.")
        except ValueError:
            errors.append("Minimum stock must be a whole number.")

        if Product.query.filter_by(sku=sku).first():
            errors.append(f"A product with SKU '{sku}' already exists.")
        if Product.query.filter_by(product_code=product_code).first():
            errors.append(f"A product with Product Code '{product_code}' already exists.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('products/form.html', suppliers=suppliers, locations=locations, categories=categories, product=None)

        # Handle product image upload if provided
        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename and allowed_image(image_file.filename):
            ext = image_file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(datetime.now(timezone.utc).timestamp())
            clean_sku = "".join(c for c in sku if c.isalnum() or c in ('-', '_'))
            image_filename = f"{clean_sku}_{timestamp}.{ext}"
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, image_filename))

        # Create product
        product = Product(
            product_code=product_code,
            sku=sku,
            name=name,
            category=category,
            description=description,
            price=price_val,
            stock_quantity=stock_val,
            minimum_stock=min_val,
            supplier_id=supplier_id,
            location_id=location_id,
            qr_code=sku,
            image_filename=image_filename
        )

        db.session.add(product)
        db.session.flush() # get product.id

        # Save physical QR code image to disk in static/qrcodes/
        qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
        save_qr_image(sku, os.path.join(qr_dir, f"{sku}.png"))

        # If initial stock > 0, log an initial stock in transaction for consistency!
        if stock_val > 0:
            tx = InventoryTransaction(
                product_id=product.id,
                transaction_type='STOCK_IN',
                quantity=stock_val,
                reference_number=f"INIT-{sku}",
                supplier_id=supplier_id,
                performed_by=current_user.id,
                notes="Initial inventory setup upon product creation",
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(tx)

        db.session.commit()
        flash(f"Product '{product.name}' created successfully with SKU: {product.sku}!", 'success')
        return redirect(url_for('products.detail', id=product.id))

    return render_template('products/form.html', suppliers=suppliers, locations=locations, categories=categories, product=None)


@products_bp.route('/products/<int:id>')
@login_required
def detail(id):
    product = Product.query.get_or_404(id)
    # Generate on-demand QR code base64
    qr_base64 = generate_qr_base64(product.sku, box_size=8)
    transactions = product.transactions.order_by(InventoryTransaction.created_at.desc()).limit(15).all()

    return render_template(
        'products/detail.html',
        product=product,
        qr_base64=qr_base64,
        transactions=transactions
    )


@products_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@role_required('ADMIN')
def edit(id):
    product = Product.query.get_or_404(id)
    suppliers = Supplier.query.order_by(Supplier.name.asc()).all()
    locations = WarehouseLocation.query.order_by(WarehouseLocation.warehouse_name, WarehouseLocation.zone).all()
    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all()]

    if request.method == 'POST':
        product_code = request.form.get('product_code', '').strip().upper()
        sku = request.form.get('sku', '').strip().upper()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        new_category = request.form.get('new_category', '').strip()
        if new_category:
            category = new_category

        description = request.form.get('description', '').strip()
        price = request.form.get('price', '0.0')
        minimum_stock = request.form.get('minimum_stock', '10')
        supplier_id = request.form.get('supplier_id') or None
        location_id = request.form.get('location_id') or None

        errors = []
        if not product_code:
            errors.append("Product code is required.")
        if not sku:
            errors.append("SKU is required.")
        if not name:
            errors.append("Product name is required.")
        if not category:
            errors.append("Category is required.")

        try:
            price_val = float(price)
            if price_val < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a valid number.")

        try:
            min_val = int(minimum_stock)
            if min_val < 0:
                errors.append("Minimum stock cannot be negative.")
        except ValueError:
            errors.append("Minimum stock must be a whole number.")

        existing_sku = Product.query.filter(Product.sku == sku, Product.id != id).first()
        if existing_sku:
            errors.append(f"SKU '{sku}' is already in use by another product.")

        existing_code = Product.query.filter(Product.product_code == product_code, Product.id != id).first()
        if existing_code:
            errors.append(f"Product Code '{product_code}' is already in use by another product.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('products/form.html', suppliers=suppliers, locations=locations, categories=categories, product=product)

        # Handle product image upload if provided
        image_file = request.files.get('image')
        if image_file and image_file.filename and allowed_image(image_file.filename):
            ext = image_file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(datetime.now(timezone.utc).timestamp())
            clean_sku = "".join(c for c in sku if c.isalnum() or c in ('-', '_'))
            image_filename = f"{clean_sku}_{timestamp}.{ext}"
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, image_filename))
            product.image_filename = image_filename

        product.product_code = product_code
        product.sku = sku
        product.name = name
        product.category = category
        product.description = description
        product.price = price_val
        product.minimum_stock = min_val
        product.supplier_id = supplier_id
        product.location_id = location_id
        product.qr_code = sku
        product.updated_at = datetime.now(timezone.utc)

        # Save/update physical QR code image to disk in static/qrcodes/
        qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
        save_qr_image(sku, os.path.join(qr_dir, f"{sku}.png"))

        db.session.commit()
        flash(f"Product '{product.name}' updated successfully.", 'success')
        return redirect(url_for('products.detail', id=product.id))

    return render_template('products/form.html', suppliers=suppliers, locations=locations, categories=categories, product=product)


@products_bp.route('/products/<int:id>/delete', methods=['POST'])
@role_required('ADMIN')
def delete(id):
    product = Product.query.get_or_404(id)
    if product.stock_quantity > 0:
        flash(f"Cannot delete product '{product.name}' because it currently has {product.stock_quantity} units in stock. Please dispatch remaining stock first.", 'danger')
        return redirect(url_for('products.detail', id=id))

    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{name}' was deleted successfully.", 'info')
    return redirect(url_for('products.index'))


@products_bp.route('/products/<int:id>/print-qr')
@login_required
def print_qr(id):
    product = Product.query.get_or_404(id)
    qr_base64 = generate_qr_base64(product.sku, box_size=10)
    return render_template('products/print_qr.html', product=product, qr_base64=qr_base64)
