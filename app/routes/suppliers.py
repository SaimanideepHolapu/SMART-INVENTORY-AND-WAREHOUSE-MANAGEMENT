from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, Supplier, Product, InventoryTransaction
from app.routes.auth import role_required

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers')
@login_required
def index():
    search = request.args.get('search', '').strip()
    query = Supplier.query

    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.supplier_code.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%'))
        )

    suppliers = query.order_by(Supplier.name.asc()).all()
    return render_template('suppliers/list.html', suppliers=suppliers, search=search)


@suppliers_bp.route('/suppliers/new', methods=['GET', 'POST'])
@role_required('ADMIN')
def create():
    if request.method == 'POST':
        supplier_code = request.form.get('supplier_code', '').strip().upper()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        errors = []
        if not supplier_code:
            errors.append("Supplier code is required.")
        if not name:
            errors.append("Supplier name is required.")

        if Supplier.query.filter_by(supplier_code=supplier_code).first():
            errors.append(f"Supplier code '{supplier_code}' is already registered.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('suppliers/form.html', supplier=None)

        supplier = Supplier(
            supplier_code=supplier_code,
            name=name,
            phone=phone,
            email=email,
            address=address
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f"Supplier '{supplier.name}' ({supplier.supplier_code}) created successfully!", 'success')
        return redirect(url_for('suppliers.detail', id=supplier.id))

    return render_template('suppliers/form.html', supplier=None)


@suppliers_bp.route('/suppliers/<int:id>')
@login_required
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    products = Product.query.filter_by(supplier_id=supplier.id).all()
    recent_transactions = InventoryTransaction.query.filter(
        InventoryTransaction.supplier_id == supplier.id,
        InventoryTransaction.transaction_type == 'STOCK_IN'
    ).order_by(InventoryTransaction.created_at.desc()).limit(15).all()

    return render_template(
        'suppliers/detail.html',
        supplier=supplier,
        products=products,
        recent_transactions=recent_transactions
    )


@suppliers_bp.route('/suppliers/<int:id>/edit', methods=['GET', 'POST'])
@role_required('ADMIN')
def edit(id):
    supplier = Supplier.query.get_or_404(id)

    if request.method == 'POST':
        supplier_code = request.form.get('supplier_code', '').strip().upper()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        errors = []
        if not supplier_code:
            errors.append("Supplier code is required.")
        if not name:
            errors.append("Supplier name is required.")

        existing = Supplier.query.filter(Supplier.supplier_code == supplier_code, Supplier.id != id).first()
        if existing:
            errors.append(f"Supplier code '{supplier_code}' is already taken.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('suppliers/form.html', supplier=supplier)

        supplier.supplier_code = supplier_code
        supplier.name = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        flash(f"Supplier '{supplier.name}' updated successfully.", 'success')
        return redirect(url_for('suppliers.detail', id=supplier.id))

    return render_template('suppliers/form.html', supplier=supplier)


@suppliers_bp.route('/suppliers/<int:id>/delete', methods=['POST'])
@role_required('ADMIN')
def delete(id):
    supplier = Supplier.query.get_or_404(id)
    if supplier.products:
        flash(f"Cannot delete supplier '{supplier.name}' because {len(supplier.products)} products are still associated with it. Please reassign them first.", 'danger')
        return redirect(url_for('suppliers.detail', id=id))

    name = supplier.name
    db.session.delete(supplier)
    db.session.commit()
    flash(f"Supplier '{name}' was deleted successfully.", 'info')
    return redirect(url_for('suppliers.index'))
