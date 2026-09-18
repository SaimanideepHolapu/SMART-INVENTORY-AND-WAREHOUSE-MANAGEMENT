import os
from datetime import datetime, timezone, timedelta
from app import create_app
from app.models import db, User, Supplier, WarehouseLocation, Product, InventoryTransaction

def seed_database():
    app = create_app()
    with app.app_context():
        print("Resetting database schema...")
        db.drop_all()
        db.create_all()

        print("1. Seeding User Accounts (Admin, Staff, Manager)...")
        admin_user = User(
            name="Saimanideep (Admin)",
            email="admin@warehouse.com",
            role="ADMIN",
            is_active_user=True
        )
        admin_user.set_password("admin123")

        staff_user = User(
            name="Akhil (Staff)",
            email="staff@warehouse.com",
            role="STAFF",
            is_active_user=True
        )
        staff_user.set_password("staff123")

        manager_user = User(
            name="Pranay (Manager)",
            email="manager@warehouse.com",
            role="MANAGER",
            is_active_user=True
        )
        manager_user.set_password("manager123")

        db.session.add_all([admin_user, staff_user, manager_user])
        db.session.flush()

        print("2. Seeding Suppliers...")
        suppliers = [
            Supplier(
                supplier_code="SUP-APEX-01",
                name="Apex Tech Logistics",
                phone="+1 (555) 234-8801",
                email="orders@apexlogistics.com",
                address="Building 4, Freight Terminal Blvd, Chicago, IL"
            ),
            Supplier(
                supplier_code="SUP-GLBSIL-02",
                name="Global Silicon Technologies",
                phone="+1 (555) 345-9902",
                email="supply@globalsilicon.com",
                address="800 Microchip Way, San Jose, CA"
            ),
            Supplier(
                supplier_code="SUP-PRECHW-03",
                name="Precision Hardware Ltd",
                phone="+1 (555) 456-1103",
                email="fulfillment@precisionhw.com",
                address="120 Industrial Parkway, Austin, TX"
            ),
            Supplier(
                supplier_code="SUP-NXTGEN-04",
                name="NextGen Enterprise Peripherals",
                phone="+1 (555) 567-2204",
                email="b2b@nextgenperipherals.com",
                address="45 Commercial Dock, Seattle, WA"
            ),
            Supplier(
                supplier_code="SUP-OMEGA-05",
                name="Omega Industrial Cabling",
                phone="+1 (555) 678-3305",
                email="sales@omegacables.com",
                address="99 Infrastructure Rd, Columbus, OH"
            )
        ]
        db.session.add_all(suppliers)
        db.session.flush()

        print("3. Seeding Warehouse Storage Bay Locations...")
        locations = [
            WarehouseLocation(warehouse_name="Warehouse Alpha", zone="A", aisle="01", rack="02", shelf="01"),
            WarehouseLocation(warehouse_name="Warehouse Alpha", zone="A", aisle="02", rack="01", shelf="03"),
            WarehouseLocation(warehouse_name="Warehouse Alpha", zone="B", aisle="04", rack="03", shelf="02"),
            WarehouseLocation(warehouse_name="Warehouse Alpha", zone="B", aisle="05", rack="02", shelf="01"),
            WarehouseLocation(warehouse_name="Warehouse Alpha", zone="C", aisle="01", rack="01", shelf="04"),
            WarehouseLocation(warehouse_name="Warehouse Beta", zone="A", aisle="03", rack="02", shelf="02"),
            WarehouseLocation(warehouse_name="Warehouse Beta", zone="B", aisle="01", rack="04", shelf="01"),
            WarehouseLocation(warehouse_name="Warehouse Beta", zone="C", aisle="02", rack="03", shelf="03"),
        ]
        db.session.add_all(locations)
        db.session.flush()

        print("4. Seeding Realistic Products Catalog...")
        products_data = [
            # Storage
            {
                "product_code": "PRD-STR-001",
                "sku": "SSD-NVME-1TB",
                "name": "1TB NVMe PCIe 4.0 Internal SSD",
                "category": "Storage",
                "description": "High-performance M.2 NVMe SSD up to 7,000 MB/s read speed. Bulk pack.",
                "price": 89.99,
                "stock_quantity": 85,
                "minimum_stock": 20,
                "location_id": locations[0].id,
                "supplier_id": suppliers[1].id
            },
            {
                "product_code": "PRD-STR-002",
                "sku": "HDD-SAS-2TB",
                "name": "2TB Enterprise SAS 12Gb/s 7200RPM HDD",
                "category": "Storage",
                "description": "Mission-critical server storage with 2M hour MTBF rating.",
                "price": 149.50,
                "stock_quantity": 14, # LOW STOCK (14 <= 25)
                "minimum_stock": 25,
                "location_id": locations[0].id,
                "supplier_id": suppliers[1].id
            },
            {
                "product_code": "PRD-STR-003",
                "sku": "SSD-RUG-500",
                "name": "500GB Portable Rugged USB-C SSD",
                "category": "Storage",
                "description": "IP67 dust and water resistant shockproof portable drive.",
                "price": 64.99,
                "stock_quantity": 42,
                "minimum_stock": 15,
                "location_id": locations[1].id,
                "supplier_id": suppliers[0].id
            },

            # Peripherals
            {
                "product_code": "PRD-PER-001",
                "sku": "KB-MECH-RGB",
                "name": "Mechanical Backlit Industrial Keyboard",
                "category": "Peripherals",
                "description": "Tenkeyless mechanical keyboard with Cherry MX Brown tactile switches.",
                "price": 79.99,
                "stock_quantity": 120,
                "minimum_stock": 30,
                "location_id": locations[2].id,
                "supplier_id": suppliers[3].id
            },
            {
                "product_code": "PRD-PER-002",
                "sku": "MOU-ERGO-WL",
                "name": "Wireless Ergonomic Precision Mouse",
                "category": "Peripherals",
                "description": "2.4GHz wireless rechargeable mouse with thumb scroll and high DPI sensor.",
                "price": 45.00,
                "stock_quantity": 65,
                "minimum_stock": 20,
                "location_id": locations[2].id,
                "supplier_id": suppliers[3].id
            },
            {
                "product_code": "PRD-PER-003",
                "sku": "CAM-PRO-1080",
                "name": "1080p Pro Stream Wide-Angle Webcam",
                "category": "Peripherals",
                "description": "Full HD 60fps auto-focus camera with stereo noise-canceling mic.",
                "price": 59.99,
                "stock_quantity": 8, # LOW STOCK (8 <= 20)
                "minimum_stock": 20,
                "location_id": locations[3].id,
                "supplier_id": suppliers[3].id
            },
            {
                "product_code": "PRD-PER-004",
                "sku": "AUD-ANC-PRO",
                "name": "Active Noise Cancelling USB-C Headset",
                "category": "Peripherals",
                "description": "Over-ear headset with boom microphone for operations call center.",
                "price": 119.00,
                "stock_quantity": 0, # OUT OF STOCK (0 units)
                "minimum_stock": 10,
                "location_id": locations[3].id,
                "supplier_id": suppliers[3].id
            },

            # Networking
            {
                "product_code": "PRD-NET-001",
                "sku": "NET-SW-24P",
                "name": "24-Port Gigabit Managed L2+ Switch",
                "category": "Networking",
                "description": "Rackmountable enterprise switch with 4x SFP+ 10G uplink ports.",
                "price": 389.00,
                "stock_quantity": 18,
                "minimum_stock": 10,
                "location_id": locations[4].id,
                "supplier_id": suppliers[2].id
            },
            {
                "product_code": "PRD-NET-002",
                "sku": "NET-RTR-AX",
                "name": "Wi-Fi 6 Dual-Band Mesh Router",
                "category": "Networking",
                "description": "AX3000 wireless router with WPA3 enterprise security encryption.",
                "price": 129.99,
                "stock_quantity": 6, # LOW STOCK (6 <= 15)
                "minimum_stock": 15,
                "location_id": locations[4].id,
                "supplier_id": suppliers[2].id
            },
            {
                "product_code": "PRD-NET-003",
                "sku": "CAB-CAT6-50M",
                "name": "Cat6 UTP Ethernet Spool Cable 50m",
                "category": "Networking",
                "description": "Pure bare copper stranded conductor 550MHz patch cable.",
                "price": 28.50,
                "stock_quantity": 210,
                "minimum_stock": 50,
                "location_id": locations[4].id,
                "supplier_id": suppliers[4].id
            },

            # Displays & Power
            {
                "product_code": "PRD-DIS-001",
                "sku": "MON-IPS-27-4K",
                "name": 'UltraSharp 27" 4K IPS Industrial Monitor',
                "category": "Displays & Power",
                "description": "Factory-calibrated 3840x2160 IPS panel with 99% sRGB color gamut.",
                "price": 429.00,
                "stock_quantity": 34,
                "minimum_stock": 15,
                "location_id": locations[5].id,
                "supplier_id": suppliers[0].id
            },
            {
                "product_code": "PRD-PWR-001",
                "sku": "PWR-UPS-1500",
                "name": "1500VA Smart UPS Battery Backup",
                "category": "Displays & Power",
                "description": "Pure sine-wave 900W rack/tower line-interactive battery backup.",
                "price": 275.00,
                "stock_quantity": 12,
                "minimum_stock": 8,
                "location_id": locations[5].id,
                "supplier_id": suppliers[2].id
            },

            # Components
            {
                "product_code": "PRD-CMP-001",
                "sku": "RAM-DDR5-32G",
                "name": "DDR5 32GB (2x16GB) 6000MHz Desktop RAM",
                "category": "Components",
                "description": "Dual-channel memory kit with aluminum heatspreader and Intel XMP 3.0.",
                "price": 109.99,
                "stock_quantity": 95,
                "minimum_stock": 25,
                "location_id": locations[6].id,
                "supplier_id": suppliers[1].id
            },
            {
                "product_code": "PRD-CMP-002",
                "sku": "PSU-850-GOLD",
                "name": "Fully Modular 850W 80+ Gold Power Supply",
                "category": "Components",
                "description": "ATX 3.0 certified with PCIe 5.0 12VHPWR native connector.",
                "price": 139.99,
                "stock_quantity": 28,
                "minimum_stock": 12,
                "location_id": locations[6].id,
                "supplier_id": suppliers[2].id
            },
            {
                "product_code": "PRD-CMP-003",
                "sku": "ACC-THM-4G",
                "name": "Thermal Paste Compound 4g Syringe",
                "category": "Components",
                "description": "Non-conductive carbon micro-particle thermal interface material.",
                "price": 8.99,
                "stock_quantity": 350,
                "minimum_stock": 50,
                "location_id": locations[7].id,
                "supplier_id": suppliers[2].id
            },
            {
                "product_code": "PRD-CMP-004",
                "sku": "EQP-BC-SCAN",
                "name": "Handheld Laser Barcode / QR Gun Scanner",
                "category": "Components",
                "description": "Heavy-duty industrial IP54 wireless barcode scanner with cradle.",
                "price": 165.00,
                "stock_quantity": 22,
                "minimum_stock": 10,
                "location_id": locations[7].id,
                "supplier_id": suppliers[3].id
            }
        ]

        products = []
        for pdata in products_data:
            p = Product(
                product_code=pdata["product_code"],
                sku=pdata["sku"],
                name=pdata["name"],
                category=pdata["category"],
                description=pdata["description"],
                price=pdata["price"],
                stock_quantity=pdata["stock_quantity"],
                minimum_stock=pdata["minimum_stock"],
                location_id=pdata["location_id"],
                supplier_id=pdata["supplier_id"],
                qr_code=pdata["sku"]
            )
            products.append(p)
            db.session.add(p)
        db.session.flush()

        print("5. Seeding Realistic Transaction History (Movements over past 10 days & today)...")
        now = datetime.now(timezone.utc)
        transactions = []

        # Generate realistic chronological movements
        past_movements = [
            # Day -9
            (9, products[0], "STOCK_IN", 100, "PO-2026-0101", suppliers[1].id, None, staff_user.id, "Bulk delivery from Global Silicon"),
            (9, products[3], "STOCK_IN", 150, "PO-2026-0102", suppliers[3].id, None, staff_user.id, "Inbound mechanical keyboards batch"),
            # Day -8
            (8, products[0], "STOCK_OUT", 15, "SO-2026-0201", None, "Order #4891 - Tech Corp", staff_user.id, "Customer hardware shipment"),
            (8, products[4], "STOCK_IN", 80, "PO-2026-0103", suppliers[3].id, None, staff_user.id, "Ergonomic mice container delivery"),
            # Day -7
            (7, products[9], "STOCK_IN", 250, "PO-2026-0104", suppliers[4].id, None, staff_user.id, "Network cabling inventory restock"),
            (7, products[3], "STOCK_OUT", 20, "SO-2026-0202", None, "Order #4895 - ByteWorks", staff_user.id, "Keyboard order fulfillment"),
            # Day -6
            (6, products[12], "STOCK_IN", 120, "PO-2026-0105", suppliers[1].id, None, staff_user.id, "DDR5 memory modules received"),
            (6, products[10], "STOCK_IN", 40, "PO-2026-0106", suppliers[0].id, None, staff_user.id, "4K monitors delivery"),
            # Day -5
            (5, products[12], "STOCK_OUT", 25, "SO-2026-0203", None, "Assembly Line 1", staff_user.id, "Dispatched for workstation builds"),
            (5, products[7], "STOCK_IN", 25, "PO-2026-0107", suppliers[2].id, None, staff_user.id, "Enterprise switch intake"),
            # Day -4
            (4, products[1], "STOCK_IN", 30, "PO-2026-0108", suppliers[1].id, None, staff_user.id, "SAS drives restock"),
            (4, products[1], "STOCK_OUT", 16, "SO-2026-0204", None, "Server Cluster Alpha", staff_user.id, "Storage array replacement"),
            # Day -3
            (3, products[5], "STOCK_IN", 25, "PO-2026-0109", suppliers[3].id, None, staff_user.id, "Webcams shipment"),
            (3, products[5], "STOCK_OUT", 17, "SO-2026-0205", None, "Branch North - IT Dept", staff_user.id, "Remote worker kits"),
            # Day -2
            (2, products[6], "STOCK_IN", 20, "PO-2026-0110", suppliers[3].id, None, staff_user.id, "Headsets shipment"),
            (2, products[6], "STOCK_OUT", 20, "SO-2026-0206", None, "Call Center Expansion", staff_user.id, "All units allocated and dispatched"),
            (2, products[8], "STOCK_IN", 15, "PO-2026-0111", suppliers[2].id, None, staff_user.id, "Mesh routers batch"),
            # Day -1 (Yesterday)
            (1, products[8], "STOCK_OUT", 9, "SO-2026-0207", None, "Branch South Hub", staff_user.id, "Store deployment"),
            (1, products[14], "STOCK_IN", 400, "PO-2026-0112", suppliers[2].id, None, staff_user.id, "Thermal paste master case"),
            (1, products[14], "STOCK_OUT", 50, "SO-2026-0208", None, "Repair Center", staff_user.id, "Maintenance bench supply"),
            # Day 0 (Today)
            (0, products[2], "STOCK_IN", 45, "PO-2026-0113", suppliers[0].id, None, staff_user.id, "Morning freight intake"),
            (0, products[2], "STOCK_OUT", 3, "SO-2026-0209", None, "Field Operations", staff_user.id, "Field technicians dispatch"),
            (0, products[10], "STOCK_OUT", 6, "SO-2026-0210", None, "Design Studio", staff_user.id, "VIP client deployment")
        ]

        for days_ago, prod, tx_type, qty, ref, supp_id, dest, user_id, notes in past_movements:
            tx_time = now - timedelta(days=days_ago, hours=2, minutes=15)
            tx = InventoryTransaction(
                product_id=prod.id,
                transaction_type=tx_type,
                quantity=qty,
                reference_number=ref,
                supplier_id=supp_id,
                destination=dest,
                performed_by=user_id,
                notes=notes,
                created_at=tx_time
            )
            transactions.append(tx)

        db.session.add_all(transactions)
        db.session.commit()

        print("==========================================================")
        print("DATABASE SEED COMPLETED SUCCESSFULLY!")
        print("==========================================================")
        print(f"Users created: {User.query.count()}")
        print(f"Suppliers created: {Supplier.query.count()}")
        print(f"Locations created: {WarehouseLocation.query.count()}")
        print(f"Products created: {Product.query.count()}")
        print(f"Transactions created: {InventoryTransaction.query.count()}")
        print("----------------------------------------------------------")
        print("DEMO CREDENTIALS:")
        print("  * Admin:           admin@warehouse.com    / admin123")
        print("  * Warehouse Staff: staff@warehouse.com    / staff123")
        print("  * Manager:         manager@warehouse.com  / manager123")
        print("==========================================================")

if __name__ == '__main__':
    seed_database()
