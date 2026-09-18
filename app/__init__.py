import os
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from app.models import db, User, Product

login_manager = LoginManager()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db_path = os.path.join(app.instance_path, 'warehouse.db')

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'smart-warehouse-secret-key-2026!secure-random-seed'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f'sqlite:///{db_path}'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access warehouse operations.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.products import products_bp
    from app.routes.inventory import inventory_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.locations import locations_bp
    from app.routes.transactions import transactions_bp
    from app.routes.scanner import scanner_bp
    from app.routes.reports import reports_bp
    from app.routes.analytics import analytics_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(users_bp)

    # Global context processor for notification count & status
    @app.context_processor
    def inject_global_data():
        if current_user.is_authenticated:
            low_stock_count = Product.query.filter(Product.stock_quantity <= Product.minimum_stock).count()
        else:
            low_stock_count = 0
        return {
            'low_stock_badge_count': low_stock_count
        }

    # Error handling
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto-create tables if running directly
    with app.app_context():
        db.create_all()

    return app
