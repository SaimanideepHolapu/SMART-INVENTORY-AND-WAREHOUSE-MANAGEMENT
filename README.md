# SMART INVENTORY & WAREHOUSE MANAGEMENT SYSTEM

An enterprise-grade, centralized web application engineered for high-precision warehouse logistics, real-time inventory tracking, QR/barcode identification, automated low-stock alerting, supply chain telemetry, and comprehensive reporting.

---

## 1. Problem Statement
Manual registers, disparate spreadsheets, and disconnected legacy software plague warehouse operations with:
* Inaccurate physical stock counts and phantom inventory
* Delayed detection of low-stock and depleted items leading to assembly halts
* Zero auditability over who received or dispatched stock
* Absence of physical bay, zone, and aisle coordinates for picker routing
* Inability to rapidly scan and identify products on warehouse floors

## 2. Solution Overview
The **Smart Inventory & Warehouse Management System** establishes a single, immutable source of truth for the entire supply chain lifecycle:
1. **Accurate Inventory**: Automated stock status calculation (`IN STOCK`, `LOW STOCK`, `OUT OF STOCK`).
2. **Traceable Movement**: Every single unit received (Stock In) or dispatched (Stock Out) creates an atomic audit transaction with user ID, timestamp, counterpart, and reference number.
3. **Safety Guards**: Strictly enforces non-negative stock. Over-allocation requests are rejected at both API and database layers.
4. **Instant Identification**: Live camera QR/barcode scanner via HTML5 + instant manual fallback with audio feedback.
5. **Role-Based Access Control**: Tailored workflows for `ADMIN`, `STAFF`, and `MANAGER` roles.
6. **Actionable Intelligence**: Dynamic Chart.js visualizations, financial valuations, and 1-click CSV exports for inventory, movements, and reorders.

---

## 3. Technology Stack

* **Backend**: Python 3.14 + Flask 3.1
* **Database & ORM**: SQLite (via Flask-SQLAlchemy 3.1 / SQLAlchemy 2.x), structured for direct zero-code migration to PostgreSQL.
* **Security & Auth**: Flask-Login, Werkzeug password hashing (Scrypt/PBKDF2), RBAC decorators, CSRF protection.
* **Frontend Design System**: Custom enterprise warehouse UI built with Bootstrap 5.3, FontAwesome 6, and modern CSS variables.
* **Data Visualization**: Chart.js 4.4 for real-time velocity curves, category doughnuts, and health distributions.
* **QR & Barcode Scanning**: `html5-qrcode` engine with Web Audio API synthesizer feedback + `qrcode` Python library for dynamic on-the-fly base64 generation and thermal printable sticker layouts.

---

## 4. Key Modules & Features

| Module | Features & Capabilities |
| :--- | :--- |
| **Operations Dashboard** | 6 live KPI widgets, 7-day movement velocity chart, category distribution doughnut, low-stock urgent alert cards, and real-time movement ledger. |
| **Live Inventory** | Real-time unit counts, dynamic badges, category filter, instant filter pills (`All`, `In Stock`, `Low Stock`, `Out of Stock`), and quick intake/dispatch buttons. |
| **Material Intake (Stock In)** | Atomic increment, auto-calculated projected stock balance, vendor selection, PO reference number auto-generation, and audit trail commit. |
| **Material Dispatch (Stock Out)**| Atomic decrement, real-time over-allocation guard preventing negative stock, destination tracking, and dispatch reference logging. |
| **QR & Barcode Scanner Hub** | Camera scanner with audio beep, manual barcode search, and instant product card with 1-click Stock In / Stock Out buttons. |
| **Product Master Catalog** | Comprehensive SKU registry, unit cost, MSRP, minimum alert thresholds, warehouse bay mapping, base64 QR code preview, and printable label view. |
| **Supplier Directory** | Vendor profiles, contact details, supplied product catalogs, and inbound shipment fulfillment history. |
| **Warehouse Location Topology** | Facility, Zone, Aisle, Rack, and Shelf coordinates with mapped product quantities. |
| **Audit Trail Ledger** | Searchable history with date range, movement type, product, and operator filters. |
| **Reports Center** | 3 specialized reports (Inventory Valuation, Stock Movements, Low-Stock Reorder) with **1-Click CSV Exports**. |
| **Supply Chain Analytics** | 14-day velocity trends, stock health breakdown, fastest-moving products, and category capital share. |
| **User & Role Management** | Admin module for registering staff, changing RBAC roles, and deactivating accounts. |

---

## 5. Database Architecture & Schema

```text
  [USERS]
     id (PK), name, email (UK), password_hash, role (ADMIN|STAFF|MANAGER), is_active_user, created_at
       │
       └──< performs >──┐
                        ▼
  [SUPPLIERS] ──< supplies >── [PRODUCTS] ──< recorded_in >── [INVENTORY_TRANSACTIONS]
     id (PK)                     id (PK)                         id (PK)
     supplier_code (UK)          product_code (UK)               product_id (FK)
     name, phone, email          sku (UK)                        transaction_type (STOCK_IN | STOCK_OUT)
     address                     name, category, price           quantity
                                 stock_quantity, minimum_stock   reference_number
                                 location_id (FK)                supplier_id (FK, nullable)
                                 supplier_id (FK)                destination (nullable)
                                 qr_code                         performed_by (FK -> USERS)
                                    │                            notes, created_at
                                    ▼
                        [WAREHOUSE_LOCATIONS]
                           id (PK), warehouse_name, zone, aisle, rack, shelf
```

### Dynamic Stock Status Engine
Stock status is never manually entered; it is computed deterministically:
* `stock_quantity == 0` &rarr; **`OUT OF STOCK`** (Red)
* `stock_quantity <= minimum_stock` &rarr; **`LOW STOCK`** (Amber)
* `stock_quantity > minimum_stock` &rarr; **`IN STOCK`** (Green)

---

## 6. Demo Accounts & Credentials

The database includes three pre-configured accounts:

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@warehouse.com` | `admin123` | Full access: Master data, products, suppliers, bays, users, stock operations, reports, analytics. |
| **Warehouse Staff** | `staff@warehouse.com` | `staff123` | Operational access: Dashboard, catalog, live inventory, stock in, stock out, QR scanner, audit logs. |
| **Manager** | `manager@warehouse.com` | `manager123` | Supervisory access: Dashboard, inventory visibility, suppliers, transactions, reports, CSV exports, analytics. |

> **Note**: The login screen features **1-Click Instant Demo Login Buttons** allowing immediate switching between roles during live demonstrations without typing.

---

## 7. Installation & Quick Start

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.14)
* pip package manager

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Database with Realistic Data
Populates 16 realistic enterprise products across 5 categories, 5 suppliers, 8 warehouse bays, 3 demo accounts, and 23 past transactions:
```bash
python seed.py
```

### 4. Run the Web Application
```bash
python run.py
```
Open your browser at **`http://127.0.0.1:5000`**

### 5. Run Automated Tests
```bash
python -m pytest tests/ -v
```

---

## 8. Live Demonstration Walkthrough

Follow this 9-step scenario to evaluate the system end-to-end:

1. **Sign In**: Navigate to `http://127.0.0.1:5000/login` and click **Warehouse Staff** (or login with `staff@warehouse.com` / `staff123`).
2. **Explore Dashboard**: Review the 6 real-time KPI counters (Total Products: 16, Low Stock: 3, Out of Stock: 1), velocity charts, and the dedicated **Low-Stock Alert Panel**.
3. **Inspect Product**: Click on `Mechanical Backlit Industrial Keyboard` (`KB-MECH-RGB`). Notice the dynamic stock badge, physical bay location (`Warehouse Alpha > Zone B > Aisle 04`), supplier, generated QR code, and recent movement ledger. Click **Warehouse Sticker Label** to view the thermal printer layout.
4. **Perform Stock In (Intake)**:
   - Click **Stock In** from the top navbar or product page.
   - Select `KB-MECH-RGB`, enter Quantity: `50`, Reference: `PO-2026-DEMO1`.
   - Submit and verify inventory increments from `120` to `170 units` with an audit record created.
5. **Perform Stock Out (Dispatch)**:
   - Click **Stock Out**.
   - Select `KB-MECH-RGB`, enter Quantity: `40`, Destination: `Customer Order #8821`, Reference: `SO-2026-DEMO2`.
   - Submit and confirm stock decreases to `130 units`.
6. **Test Safety Guard**:
   - Attempt to dispatch `200 units` of `KB-MECH-RGB` (when only 130 are available).
   - Observe the live UI warning, disabled submit button, and backend validation rejection (`Insufficient stock`).
7. **Test QR / Barcode Scanner**:
   - Navigate to **QR / Barcode Hub** (`/scanner`).
   - In the manual lookup field, paste `SSD-NVME-1TB` and press Enter (or start camera to scan physical QR).
   - View the instant product card, stock status, and execute quick operations.
8. **View Reports & Export CSV**:
   - Navigate to **Reports & CSV** (`/reports`).
   - Inspect the **Inventory Valuation Report**, **Stock Movement Audit**, and **Low-Stock Reorder Report**.
   - Click **Download Inventory CSV** to verify standard CSV generation.
9. **Verify Real-Time Synchronization**:
   - Return to the Dashboard and observe updated movements (+50 in, -40 out) reflected across all charts and metrics.
