import pytest
from app import create_app
from app.models import db, User, Supplier, WarehouseLocation, Product, InventoryTransaction
from app.services.inventory_service import (
    perform_stock_in,
    perform_stock_out,
    InsufficientStockError,
    get_kpis
)
from app.services.report_service import generate_inventory_csv, generate_movement_csv

@pytest.fixture
def app():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        db.create_all()

        # Seed test user
        admin = User(name="Admin User", email="admin@test.com", role="ADMIN")
        admin.set_password("adminpass")
        staff = User(name="Staff User", email="staff@test.com", role="STAFF")
        staff.set_password("staffpass")
        db.session.add_all([admin, staff])
        db.session.flush()

        # Seed supplier & location
        supp = Supplier(supplier_code="SUP-TEST-1", name="Acme Components", phone="1234", email="test@acme.com")
        loc = WarehouseLocation(warehouse_name="Main WH", zone="A", aisle="01", rack="01", shelf="01")
        db.session.add_all([supp, loc])
        db.session.flush()

        # Seed test products
        p1 = Product(
            product_code="PRD-01",
            sku="SKU-TEST-KEYBOARD",
            name="USB Mechanical Keyboard",
            category="Peripherals",
            price=50.0,
            stock_quantity=100,
            minimum_stock=20,
            location_id=loc.id,
            supplier_id=supp.id
        )
        p2 = Product(
            product_code="PRD-02",
            sku="SKU-TEST-MOUSE",
            name="Wireless Mouse",
            category="Peripherals",
            price=25.0,
            stock_quantity=5, # LOW STOCK (5 <= 10)
            minimum_stock=10,
            location_id=loc.id,
            supplier_id=supp.id
        )
        p3 = Product(
            product_code="PRD-03",
            sku="SKU-TEST-CABLE",
            name="HDMI Cable",
            category="Accessories",
            price=10.0,
            stock_quantity=0, # OUT OF STOCK
            minimum_stock=15,
            location_id=loc.id,
            supplier_id=supp.id
        )
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_dynamic_stock_status(app):
    with app.app_context():
        p1 = Product.query.filter_by(sku="SKU-TEST-KEYBOARD").first()
        p2 = Product.query.filter_by(sku="SKU-TEST-MOUSE").first()
        p3 = Product.query.filter_by(sku="SKU-TEST-CABLE").first()

        assert p1.status == "IN STOCK"
        assert p1.is_low_stock is False
        assert p1.is_out_of_stock is False

        assert p2.status == "LOW STOCK"
        assert p2.is_low_stock is True
        assert p2.is_out_of_stock is False

        assert p3.status == "OUT OF STOCK"
        assert p3.is_low_stock is False
        assert p3.is_out_of_stock is True

def test_atomic_stock_in(app):
    with app.app_context():
        p = Product.query.filter_by(sku="SKU-TEST-KEYBOARD").first()
        initial_stock = p.stock_quantity # 100
        user = User.query.filter_by(email="staff@test.com").first()

        tx, updated_product = perform_stock_in(
            product_id=p.id,
            quantity=50,
            reference_number="PO-TEST-100",
            notes="Received 50 units",
            user_id=user.id
        )

        assert updated_product.stock_quantity == initial_stock + 50
        assert tx.quantity == 50
        assert tx.transaction_type == "STOCK_IN"
        assert tx.reference_number == "PO-TEST-100"
        assert tx.performed_by == user.id

        # Verify persisted in database
        reloaded = db.session.get(Product, p.id)
        assert reloaded.stock_quantity == 150
        assert InventoryTransaction.query.filter_by(reference_number="PO-TEST-100").count() == 1

def test_atomic_stock_out(app):
    with app.app_context():
        p = Product.query.filter_by(sku="SKU-TEST-KEYBOARD").first()
        initial_stock = p.stock_quantity # 100
        user = User.query.filter_by(email="staff@test.com").first()

        tx, updated_product = perform_stock_out(
            product_id=p.id,
            quantity=40,
            destination="Customer Order #123",
            reference_number="SO-TEST-200",
            notes="Dispatched to client",
            user_id=user.id
        )

        assert updated_product.stock_quantity == initial_stock - 40
        assert tx.quantity == 40
        assert tx.transaction_type == "STOCK_OUT"
        assert tx.destination == "Customer Order #123"

        reloaded = db.session.get(Product, p.id)
        assert reloaded.stock_quantity == 60

def test_stock_out_exceeding_available_is_rejected(app):
    with app.app_context():
        p = Product.query.filter_by(sku="SKU-TEST-KEYBOARD").first() # 100 available
        user = User.query.filter_by(email="staff@test.com").first()

        with pytest.raises(InsufficientStockError) as exc_info:
            perform_stock_out(
                product_id=p.id,
                quantity=150, # Exceeds 100!
                destination="Over-dispatch order",
                reference_number="SO-FAIL",
                user_id=user.id
            )

        assert "Insufficient stock" in str(exc_info.value)
        assert exc_info.value.available == 100
        assert exc_info.value.requested == 150

        # Verify stock did not change and no transaction created
        reloaded = db.session.get(Product, p.id)
        assert reloaded.stock_quantity == 100
        assert InventoryTransaction.query.filter_by(reference_number="SO-FAIL").first() is None

def test_negative_quantity_rejected(app):
    with app.app_context():
        p = Product.query.filter_by(sku="SKU-TEST-KEYBOARD").first()
        user = User.query.filter_by(email="staff@test.com").first()

        with pytest.raises(ValueError):
            perform_stock_in(product_id=p.id, quantity=-10, user_id=user.id)

        with pytest.raises(ValueError):
            perform_stock_out(product_id=p.id, quantity=0, destination="Test", user_id=user.id)

def test_kpi_calculations(app):
    with app.app_context():
        kpis = get_kpis()
        assert kpis['total_products'] == 3
        assert kpis['total_stock_units'] == 100 + 5 + 0
        assert kpis['low_stock_count'] == 1 # p2 is 5 <= 10
        assert kpis['out_of_stock_count'] == 1 # p3 is 0

def test_csv_export_generation(app):
    with app.app_context():
        csv_content = generate_inventory_csv()
        assert "SKU-TEST-KEYBOARD" in csv_content
        assert "IN STOCK" in csv_content
        assert "OUT OF STOCK" in csv_content

def test_rbac_protection_on_users_endpoint(client, app):
    # Unauthenticated should redirect to login
    res = client.get('/users')
    assert res.status_code == 302
    assert '/login' in res.location

    # Login as Staff
    client.post('/login', data={'email': 'staff@test.com', 'password': 'staffpass'})
    # Staff cannot access Admin User Management -> 403
    res = client.get('/users')
    assert res.status_code == 403

    # Logout and login as Admin
    client.get('/logout')
    client.post('/login', data={'email': 'admin@test.com', 'password': 'adminpass'})
    # Admin can access -> 200
    res = client.get('/users')
    assert res.status_code == 200
    assert b"User &amp; Role Management" in res.data or b"User & Role Management" in res.data
