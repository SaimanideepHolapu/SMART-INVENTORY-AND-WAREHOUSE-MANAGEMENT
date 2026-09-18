from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, User
from app.routes.auth import role_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@role_required('ADMIN')
def index():
    users = User.query.order_by(User.name.asc()).all()
    return render_template('users/list.html', users=users)


@users_bp.route('/users/new', methods=['GET', 'POST'])
@role_required('ADMIN')
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'STAFF').upper()

        errors = []
        if not name:
            errors.append("User name is required.")
        if not email:
            errors.append("Email address is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if role not in ['ADMIN', 'STAFF', 'MANAGER']:
            errors.append("Invalid user role selected.")

        if User.query.filter_by(email=email).first():
            errors.append(f"A user with email '{email}' already exists.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('users/form.html', user=None)

        user = User(
            name=name,
            email=email,
            role=role,
            is_active_user=True
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        flash(f"User '{user.name}' ({user.email}) created successfully with role {user.role}!", 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=None)


@users_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@role_required('ADMIN')
def edit(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', 'STAFF').upper()
        new_password = request.form.get('password', '').strip()
        is_active = bool(request.form.get('is_active'))

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if role not in ['ADMIN', 'STAFF', 'MANAGER']:
            errors.append("Invalid role.")

        existing = User.query.filter(User.email == email, User.id != id).first()
        if existing:
            errors.append(f"Email '{email}' is in use by another user.")

        # Guard: do not allow the current user to deactivate themselves or demote themselves if they are the only admin
        if user.id == current_user.id:
            if not is_active:
                errors.append("You cannot deactivate your own active admin account.")
            if role != 'ADMIN':
                errors.append("You cannot change your own role away from ADMIN.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('users/form.html', user=user)

        user.name = name
        user.email = email
        user.role = role
        user.is_active_user = is_active

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters long.", 'danger')
                return render_template('users/form.html', user=user)
            user.set_password(new_password)

        db.session.commit()
        flash(f"User '{user.name}' updated successfully.", 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=user)
