-- Create database
CREATE DATABASE IF NOT EXISTS rawas_realestate;
USE rawas_realestate;

-- Projects table
CREATE TABLE Projects (
    project_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    location VARCHAR(300) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status ENUM('Planning', 'Under Construction', 'Completed', 'On Hold') DEFAULT 'Planning',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Employees table
CREATE TABLE Employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    position VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(150) UNIQUE,
    salary DECIMAL(10,2),
    branch VARCHAR(100),
    hire_date DATE DEFAULT (CURRENT_DATE),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Buildings table
CREATE TABLE Buildings (
    building_id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    building_number VARCHAR(50) NOT NULL,
    building_name VARCHAR(150),
    floors_count INT NOT NULL CHECK (floors_count > 0),
    construction_status ENUM('Not Started', 'Foundation', 'Structure', 'Finishing', 'Completed') DEFAULT 'Not Started',
    completion_percentage INT DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE,
    UNIQUE KEY (project_id, building_number)
);

-- Units table
CREATE TABLE Units (
    unit_id INT PRIMARY KEY AUTO_INCREMENT,
    building_id INT NOT NULL,
    unit_number VARCHAR(20) NOT NULL,
    type ENUM('Apartment', 'Office', 'Shop', 'Studio') NOT NULL,
    area_m2 DECIMAL(8,2) NOT NULL CHECK (area_m2 > 0),
    floor INT NOT NULL,
    bedrooms INT DEFAULT 0,
    bathrooms INT DEFAULT 1,
    price DECIMAL(12,2) NOT NULL CHECK (price > 0),
    status ENUM('Available', 'Reserved', 'Sold', 'Under Maintenance') DEFAULT 'Available',
    features TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES Buildings(building_id) ON DELETE CASCADE,
    UNIQUE KEY (building_id, unit_number)
);

-- Clients table
CREATE TABLE Clients (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    national_id VARCHAR(20) UNIQUE,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(150) UNIQUE,
    address TEXT,
    client_type ENUM('Investor', 'Buyer', 'Entity') DEFAULT 'Buyer',
    registration_date DATE DEFAULT (CURRENT_DATE),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales/Contracts table
CREATE TABLE Sales (
    sale_id INT PRIMARY KEY AUTO_INCREMENT,
    unit_id INT NOT NULL UNIQUE,
    client_id INT NOT NULL,
    agent_id INT NOT NULL,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_date DATE NOT NULL,
    total_price DECIMAL(12,2) NOT NULL CHECK (total_price > 0),
    down_payment DECIMAL(12,2) NOT NULL,
    remaining_balance DECIMAL(12,2) NOT NULL,
    payment_plan TEXT,
    status ENUM('Active', 'Completed', 'Cancelled', 'Defaulted') DEFAULT 'Active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES Units(unit_id) ON DELETE RESTRICT,
    FOREIGN KEY (client_id) REFERENCES Clients(client_id) ON DELETE RESTRICT,
    FOREIGN KEY (agent_id) REFERENCES Employees(employee_id) ON DELETE RESTRICT
);

-- Payments table
CREATE TABLE Payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    payment_method ENUM('Cash', 'Bank Transfer', 'Check', 'Credit Card') NOT NULL,
    receipt_number VARCHAR(50) UNIQUE,
    due_date DATE,
    late_fee DECIMAL(10,2) DEFAULT 0,
    status ENUM('Paid', 'Pending', 'Overdue') DEFAULT 'Pending',
    notes TEXT,
    recorded_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES Sales(sale_id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES Employees(employee_id) ON DELETE SET NULL
);

-- Suppliers table
CREATE TABLE Suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(150),
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(150),
    address TEXT,
    supplier_type ENUM('Construction', 'Electrical', 'Plumbing', 'Finishing') DEFAULT 'Construction',
    rating INT CHECK (rating >= 1 AND rating <= 5),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials table
CREATE TABLE Materials (
    material_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0),
    min_quantity INT DEFAULT 10,
    max_quantity INT DEFAULT 1000,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses table
CREATE TABLE Warehouses (
    warehouse_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(300) NOT NULL,
    capacity DECIMAL(12,2) NOT NULL,
    project_id INT,
    warehouse_type ENUM('Central', 'Project') DEFAULT 'Central',
    manager_id INT,
    status ENUM('Active', 'Full', 'Closed') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES Employees(employee_id) ON DELETE SET NULL
);

-- Inventory table
CREATE TABLE Inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    warehouse_id INT NOT NULL,
    material_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES Warehouses(warehouse_id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES Materials(material_id) ON DELETE CASCADE,
    UNIQUE KEY (warehouse_id, material_id)
);

-- Purchase Orders table
CREATE TABLE PurchaseOrders (
    po_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL,
    expected_date DATE,
    status ENUM('Pending', 'Approved', 'Received', 'Cancelled') DEFAULT 'Pending',
    total_amount DECIMAL(12,2) DEFAULT 0,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES Warehouses(warehouse_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES Employees(employee_id) ON DELETE SET NULL
);

-- Purchase Items table
CREATE TABLE PurchaseItems (
    po_item_id INT PRIMARY KEY AUTO_INCREMENT,
    po_id INT NOT NULL,
    material_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    received_quantity DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (po_id) REFERENCES PurchaseOrders(po_id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES Materials(material_id) ON DELETE RESTRICT
);

-- Inventory Movements table
CREATE TABLE InventoryMovements (
    move_id INT PRIMARY KEY AUTO_INCREMENT,
    material_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL CHECK (quantity != 0),
    move_type ENUM('IN', 'OUT', 'TRANSFER', 'ADJUSTMENT') NOT NULL,
    reference_type ENUM('Purchase', 'Project', 'Adjustment', 'Transfer') NOT NULL,
    reference_id INT,
    move_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES Materials(material_id) ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES Warehouses(warehouse_id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES Employees(employee_id) ON DELETE SET NULL
);
CREATE INDEX idx_projects_status ON Projects(status);
CREATE INDEX idx_projects_location ON Projects(location);
CREATE INDEX idx_projects_dates ON Projects(start_date, end_date);
CREATE INDEX idx_buildings_project ON Buildings(project_id);
CREATE INDEX idx_buildings_status ON Buildings(construction_status);
CREATE INDEX idx_units_building ON Units(building_id);
CREATE INDEX idx_units_status ON Units(status);
CREATE INDEX idx_units_price ON Units(price);
CREATE INDEX idx_units_type ON Units(type);

CREATE INDEX idx_sales_client ON Sales(client_id);
CREATE INDEX idx_sales_agent ON Sales(agent_id);
CREATE INDEX idx_sales_status ON Sales(status);
CREATE INDEX idx_sales_date ON Sales(contract_date);
CREATE INDEX idx_payments_sale ON Payments(sale_id);
CREATE INDEX idx_payments_status ON Payments(status);
CREATE INDEX idx_payments_date ON Payments(payment_date, due_date);

CREATE INDEX idx_inventory_warehouse ON Inventory(warehouse_id);
CREATE INDEX idx_inventory_material ON Inventory(material_id);
INSERT INTO Projects (name, location, start_date, end_date, status, description) VALUES
('Ramallah Gardens', 'Ramallah, Al-Masyoun', '2024-01-15', '2025-12-31', 'Under Construction', 'Luxury residential project with 4 towers'),
('Hebron Commercial Tower', 'Hebron, City Center', '2023-06-01', '2024-11-30', 'Completed', '10-floor commercial tower for offices and shops'),
('Nablus Residential Project', 'Nablus, Rafidia', '2024-03-01', '2026-06-30', 'Planning', 'Residential complex with 8 buildings');

INSERT INTO Employees (name, position, phone, email, salary, branch) VALUES
('Ahmed Mohamed', 'Sales Manager', '0599111222', 'ahmed@rawas.ps', 5000.00, 'Ramallah'),
('Sara Khaled', 'Project Coordinator', '0599333444', 'sara@rawas.ps', 4000.00, 'Hebron'),
('Mahmoud Abdullah', 'Warehouse Manager', '0599555666', 'mahmoud@rawas.ps', 4500.00, 'Nablus');

INSERT INTO Buildings (project_id, building_number, building_name, floors_count, construction_status, completion_percentage) VALUES
(1, 'B1', 'North Tower', 8, 'Structure', 60),
(1, 'B2', 'South Tower', 8, 'Foundation', 30),
(1, 'B3', 'East Tower', 6, 'Not Started', 0);
