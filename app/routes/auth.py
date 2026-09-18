from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

def role_required(*allowed_roles):
    """
    Decorator to restrict route access to users with specified role(s).
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')

            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}! Logged in as {user.role}.', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/demo-login/<role>', methods=['GET', 'POST'])
def demo_login(role):
    """
    Convenience endpoint for live demo testing: logs in directly as admin, staff, or manager.
    """
    role_map = {
        'admin': 'admin@warehouse.com',
        'staff': 'staff@warehouse.com',
        'manager': 'manager@warehouse.com'
    }
    target_email = role_map.get(role.lower())
    if not target_email:
        flash('Invalid demo role requested.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=target_email).first()
    if user:
        login_user(user)
        flash(f'Switched to Demo Account: {user.name} ({user.role})', 'info')
        return redirect(url_for('dashboard.index'))
    else:
        flash('Demo account not found. Please run seed.py first.', 'warning')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))
