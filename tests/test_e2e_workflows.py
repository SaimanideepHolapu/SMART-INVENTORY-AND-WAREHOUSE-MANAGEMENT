import pytest
from app import create_app
from app.models import db, User, Product, InventoryTransaction

@pytest.fixture
def client():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'e2e-secret-key',
        'WTF_CSRF_ENABLED': False
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        # Import seed logic or seed minimal dataset
        from seed import seed_database
        # Run seed in this app context
        from app.models import Supplier, WarehouseLocation

        admin = User(name="Alex Thorne (Admin)", email="admin@warehouse.com", role="ADMIN")
        admin.set_password("admin123")
        staff = User(name="Marcus Vance (Staff)", email="staff@warehouse.com", role="STAFF")
        staff.set_password("staff123")
        manager = User(name="Elena Rostova (Manager)", email="manager@warehouse.com", role="MANAGER")
        manager.set_password("manager123")

        db.session.add_all([admin, staff, manager])
        db.session.flush()

        supp = Supplier(supplier_code="SUP-TEST-01", name="Apex Test Supplier", phone="555-1234", email="apex@test.com")
        loc = WarehouseLocation(warehouse_name="Warehouse Alpha", zone="A", aisle="01", rack="02", shelf="01")
        db.session.add_all([supp, loc])
        db.session.flush()

        p1 = Product(
            product_code="PRD-01",
            sku="SSD-NVME-1TB",
            name="1TB NVMe PCIe 4.0 Internal SSD",
            category="Storage",
            price=89.99,
            stock_quantity=50,
            minimum_stock=20,
            location_id=loc.id,
            supplier_id=supp.id,
            qr_code="SSD-NVME-1TB"
        )
        p2 = Product(
            product_code="PRD-02",
            sku="KB-MECH-RGB",
            name="Mechanical Backlit Industrial Keyboard",
            category="Peripherals",
            price=79.99,
            stock_quantity=8, # LOW STOCK (8 <= 15)
            minimum_stock=15,
            location_id=loc.id,
            supplier_id=supp.id,
            qr_code="KB-MECH-RGB"
        )
        p3 = Product(
            product_code="PRD-03",
            sku="AUD-ANC-PRO",
            name="Active Noise Cancelling Headset",
            category="Peripherals",
            price=119.00,
            stock_quantity=0, # OUT OF STOCK
            minimum_stock=10,
            location_id=loc.id,
            supplier_id=supp.id,
            qr_code="AUD-ANC-PRO"
        )
        db.session.add_all([p1, p2, p3])
        db.session.flush()

        tx1 = InventoryTransaction(
            product_id=p1.id,
            transaction_type="STOCK_IN",
            quantity=50,
            reference_number="PO-INIT-01",
            supplier_id=supp.id,
            performed_by=admin.id,
            notes="Initial intake"
        )
        db.session.add(tx1)
        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()

def test_demo_login_and_dashboard(client):
    # Test 1-click demo login for staff
    res = client.get('/demo-login/staff', follow_redirects=True)
    assert res.status_code == 200
    assert b"Operations Command Center" in res.data
    assert b"Marcus Vance (Staff)" in res.data

    # Test Dashboard Chart Data API
    res_charts = client.get('/api/dashboard/chart-data')
    assert res_charts.status_code == 200
    json_data = res_charts.get_json()
    assert 'trends' in json_data
    assert 'categories' in json_data
    assert 'Storage' in json_data['categories']['labels']

    # Test Notifications API
    res_notif = client.get('/api/notifications')
    assert res_notif.status_code == 200
    notif_data = res_notif.get_json()
    assert notif_data['count'] == 2 # 1 low stock + 1 out of stock

def test_complete_demo_workflow_end_to_end(client):
    """
    Simulates the exact steps from Section 29 (DEMO SCENARIO):
    1. Login as warehouse staff
    2. Open dashboard
    3. Search for product details
    4. Perform Stock In (+50)
    5. Perform Stock Out (-40)
    6. Open transaction history and verify both records
    7. Scan / search product QR code
    8. Open reports and download CSV
    9. Verify dashboard statistics updated
    """
    # Step 1: Login as warehouse staff
    login_res = client.post('/login', data={'email': 'staff@warehouse.com', 'password': 'staff123'}, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Operations Command Center" in login_res.data

    # Step 2: Check dashboard stats
    assert b"Total Products" in login_res.data
    assert b"Low Stock Items" in login_res.data

    # Step 3: Search for product details
    search_res = client.get('/products?search=Keyboard')
    assert search_res.status_code == 200
    assert b"KB-MECH-RGB" in search_res.data

    # Step 4: Perform Stock In (+50 on Keyboard)
    # Current stock is 8, +50 should yield 58 units
    stock_in_res = client.post('/inventory/stock-in', data={
        'product_id': 2,
        'quantity': 50,
        'reference_number': 'PO-DEMO-TEST-1',
        'notes': 'Demo Intake'
    }, follow_redirects=True)
    assert stock_in_res.status_code == 200
    assert b"Successfully received +50 units" in stock_in_res.data

    # Step 5: Perform Stock Out (-40 on Keyboard)
    # Stock goes from 58 -> 18 units
    stock_out_res = client.post('/inventory/stock-out', data={
        'product_id': 2,
        'quantity': 40,
        'destination': 'Customer Demo Dispatch',
        'reference_number': 'SO-DEMO-TEST-2',
        'notes': 'Demo Dispatch'
    }, follow_redirects=True)
    assert stock_out_res.status_code == 200
    assert b"Successfully dispatched -40 units" in stock_out_res.data

    # Step 5b: Verify Over-allocation prevention (Safety Guard)
    # Keyboard now has 18 units. Attempt to dispatch 50 units!
    fail_res = client.post('/inventory/stock-out', data={
        'product_id': 2,
        'quantity': 50,
        'destination': 'Excess Request',
        'reference_number': 'SO-FAIL-01'
    }, follow_redirects=True)
    assert fail_res.status_code == 200
    assert b"Insufficient stock: Available: 18, Requested: 50" in fail_res.data

    # Step 6: Open transaction history
    tx_res = client.get('/transactions')
    assert tx_res.status_code == 200
    assert b"PO-DEMO-TEST-1" in tx_res.data
    assert b"SO-DEMO-TEST-2" in tx_res.data
    assert b"Customer Demo Dispatch" in tx_res.data

    # Step 7: Scan / Search QR code via API lookup
    lookup_res = client.get('/api/lookup/KB-MECH-RGB')
    assert lookup_res.status_code == 200
    data = lookup_res.get_json()
    assert data['success'] is True
    assert data['product']['sku'] == 'KB-MECH-RGB'
    assert data['product']['stock_quantity'] == 18 # 8 + 50 - 40 = 18

    # Step 8: Open reports & download CSV
    rep_res = client.get('/reports?tab=inventory')
    assert rep_res.status_code == 200

    csv_res = client.get('/reports/inventory/csv')
    assert csv_res.status_code == 200
    assert csv_res.headers['Content-Type'].startswith('text/csv')
    assert b"Product Name,SKU,Category" in csv_res.data
    assert b"KB-MECH-RGB" in csv_res.data

    # Step 9: Reopen dashboard and check updated live values
    dash_res = client.get('/dashboard')
    assert dash_res.status_code == 200
    # Today's stock in has +50, today's stock out has -40
    assert b"+50" in dash_res.data
    assert b"-40" in dash_res.data
