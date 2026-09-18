from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import db, WarehouseLocation, Product
from app.routes.auth import role_required

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/locations')
@login_required
def index():
    locations = WarehouseLocation.query.order_by(
        WarehouseLocation.warehouse_name,
        WarehouseLocation.zone,
        WarehouseLocation.aisle,
        WarehouseLocation.rack,
        WarehouseLocation.shelf
    ).all()
    return render_template('locations/list.html', locations=locations)


@locations_bp.route('/locations/new', methods=['GET', 'POST'])
@role_required('ADMIN')
def create():
    if request.method == 'POST':
        warehouse_name = request.form.get('warehouse_name', '').strip()
        zone = request.form.get('zone', '').strip().upper()
        aisle = request.form.get('aisle', '').strip().upper()
        rack = request.form.get('rack', '').strip().upper()
        shelf = request.form.get('shelf', '').strip().upper()

        if not all([warehouse_name, zone, aisle, rack, shelf]):
            flash("All location coordinates (Warehouse, Zone, Aisle, Rack, Shelf) are required.", "danger")
            return render_template('locations/form.html', location=None)

        loc = WarehouseLocation(
            warehouse_name=warehouse_name,
            zone=zone,
            aisle=aisle,
            rack=rack,
            shelf=shelf
        )
        db.session.add(loc)
        db.session.commit()
        flash(f"Warehouse location '{loc.short_code}' created successfully!", "success")
        return redirect(url_for('locations.index'))

    return render_template('locations/form.html', location=None)


@locations_bp.route('/locations/<int:id>/edit', methods=['GET', 'POST'])
@role_required('ADMIN')
def edit(id):
    loc = WarehouseLocation.query.get_or_404(id)

    if request.method == 'POST':
        loc.warehouse_name = request.form.get('warehouse_name', '').strip()
        loc.zone = request.form.get('zone', '').strip().upper()
        loc.aisle = request.form.get('aisle', '').strip().upper()
        loc.rack = request.form.get('rack', '').strip().upper()
        loc.shelf = request.form.get('shelf', '').strip().upper()

        if not all([loc.warehouse_name, loc.zone, loc.aisle, loc.rack, loc.shelf]):
            flash("All location coordinates are required.", "danger")
            return render_template('locations/form.html', location=loc)

        db.session.commit()
        flash(f"Location updated to '{loc.short_code}'.", "success")
        return redirect(url_for('locations.index'))

    return render_template('locations/form.html', location=loc)


@locations_bp.route('/locations/<int:id>/delete', methods=['POST'])
@role_required('ADMIN')
def delete(id):
    loc = WarehouseLocation.query.get_or_404(id)
    if loc.products:
        flash(f"Cannot delete location '{loc.short_code}' because {len(loc.products)} products are assigned to this bay.", "danger")
        return redirect(url_for('locations.index'))

    name = loc.short_code
    db.session.delete(loc)
    db.session.commit()
    flash(f"Location '{name}' deleted.", "info")
    return redirect(url_for('locations.index'))
