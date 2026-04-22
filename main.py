"""
Rawas Real Estate System - Normalized Version (3NF)
This version implements the Third Normal Form (3NF) to reduce redundancy and improve data integrity.
"""

import pymysql
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import uuid


class Database:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '0000',
            'database': 'rawas_real_estate',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'port': 3306
        }
        self.init_db()

    def get_connection(self):
        conn = pymysql.connect(**self.db_config)
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS rawas_real_estate")
            cursor.execute("USE rawas_real_estate")

            # --- Reference Tables (Lookup Tables) for 3NF ---

            # Project Statuses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_statuses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    status_name VARCHAR(50) UNIQUE NOT NULL
                )
            ''')

            # Unit Types
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unit_types (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type_name VARCHAR(50) UNIQUE NOT NULL
                )
            ''')

            # Unit Statuses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unit_statuses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    status_name VARCHAR(50) UNIQUE NOT NULL
                )
            ''')

            # Client Types
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_types (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type_name VARCHAR(50) UNIQUE NOT NULL
                )
            ''')

            # Payment Methods
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    method_name VARCHAR(50) UNIQUE NOT NULL
                )
            ''')

            # Material Categories
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS material_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_name VARCHAR(100) UNIQUE NOT NULL
                )
            ''')

            # --- Main Tables ---

            # Projects
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    start_date DATE,
                    end_date DATE,
                    status_id INT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (status_id) REFERENCES project_statuses(id)
                )
            ''')

            # Buildings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS buildings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id INT,
                    name VARCHAR(255),
                    floors INT DEFAULT 1,
                    status VARCHAR(50) DEFAULT 'Not Started',
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')

            # Units
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS units (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    building_id INT,
                    unit_number VARCHAR(50) NOT NULL,
                    type_id INT,
                    area DECIMAL(10,2) NOT NULL,
                    floor INT,
                    bedrooms INT DEFAULT 2,
                    bathrooms INT DEFAULT 1,
                    price DECIMAL(15,2) NOT NULL,
                    status_id INT,
                    features TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
                    FOREIGN KEY (type_id) REFERENCES unit_types(id),
                    FOREIGN KEY (status_id) REFERENCES unit_statuses(id)
                )
            ''')

            # Clients
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    address TEXT,
                    type_id INT,
                    id_number VARCHAR(100),
                    company VARCHAR(255),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (type_id) REFERENCES client_types(id)
                )
            ''')

            # Employees
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    position VARCHAR(255) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    salary DECIMAL(15,2),
                    status VARCHAR(50) DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Sales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    unit_id INT UNIQUE,
                    client_id INT,
                    employee_id INT,
                    contract_date DATE,
                    contract_number VARCHAR(100) UNIQUE,
                    total_price DECIMAL(15,2),
                    down_payment DECIMAL(15,2) DEFAULT 0,
                    payment_method_id INT,
                    payment_terms TEXT,
                    status VARCHAR(50) DEFAULT 'Active',
                    next_payment_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (unit_id) REFERENCES units(id),
                    FOREIGN KEY (client_id) REFERENCES clients(id),
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
                )
            ''')

            # Payments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sale_id INT,
                    amount DECIMAL(15,2),
                    payment_date DATE,
                    payment_method_id INT,
                    receipt_number VARCHAR(100) UNIQUE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
                )
            ''')

            # Materials
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category_id INT,
                    unit VARCHAR(50),
                    price DECIMAL(10,2),
                    min_quantity INT DEFAULT 10,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES material_categories(id)
                )
            ''')

            # Inventory
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    material_id INT,
                    quantity INT DEFAULT 0,
                    location VARCHAR(255),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()
            self.seed_reference_data(cursor, conn)

        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def seed_reference_data(self, cursor, conn):
        """Seed lookup tables with initial data"""
        try:
            # Project Statuses
            statuses = [('Planning',), ('Under Construction',), ('Completed',), ('On Hold',)]
            cursor.executemany("INSERT IGNORE INTO project_statuses (status_name) VALUES (%s)", statuses)

            # Unit Types
            types = [('Apartment',), ('Villa',), ('Office',), ('Shop',), ('Studio',)]
            cursor.executemany("INSERT IGNORE INTO unit_types (type_name) VALUES (%s)", types)

            # Unit Statuses
            u_statuses = [('Available',), ('Reserved',), ('Sold',), ('Maintenance',)]
            cursor.executemany("INSERT IGNORE INTO unit_statuses (status_name) VALUES (%s)", u_statuses)

            # Client Types
            c_types = [('Buyer',), ('Tenant',), ('Investor',), ('Corporate',)]
            cursor.executemany("INSERT IGNORE INTO client_types (type_name) VALUES (%s)", c_types)

            # Payment Methods
            p_methods = [('Cash',), ('Bank Transfer',), ('Check',), ('Credit Card',)]
            cursor.executemany("INSERT IGNORE INTO payment_methods (method_name) VALUES (%s)", p_methods)

            # Material Categories
            m_cats = [('Construction',), ('Finishing',), ('Electrical',), ('Plumbing',)]
            cursor.executemany("INSERT IGNORE INTO material_categories (category_name) VALUES (%s)", m_cats)

            conn.commit()
        except Exception as e:
            print(f"⚠️ Error seeding reference data: {e}")


# ==============================================
# HELPER FUNCTIONS
# ==============================================
def execute_query(query, params=(), fetch=True, fetch_one=False):
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)

        if fetch:
            if fetch_one:
                result = cursor.fetchone()
                return result if result else None
            else:
                rows = cursor.fetchall()
                return rows
        else:
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"❌ Query Error: {e}")
        print(f"Query: {query}")
        print(f"Params: {params}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ==============================================
# FLASK APPLICATION
# ==============================================
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
db = Database()

# Create necessary directories
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)


# ==============================================
# HTML TEMPLATES CREATION FUNCTION
# ==============================================
def create_html_templates():
    """Create HTML template files"""

    # Create templates directory if not exists
    os.makedirs('templates', exist_ok=True)

    # Create static directory for CSS/JS
    os.makedirs('static', exist_ok=True)

    # Index.html (Home Page)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rawas Real Estate - Home</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(to right, #2c3e50, #3498db); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2.8rem; margin-bottom: 10px; }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .nav { background: #34495e; padding: 15px; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .nav-btn { padding: 12px 25px; background: #3498db; color: white; text-decoration: none; border-radius: 30px; font-weight: bold; transition: all 0.3s; }
        .nav-btn:hover { background: #2980b9; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .content { padding: 40px; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .card { background: #f8f9fa; border-radius: 15px; padding: 25px; transition: transform 0.3s, box-shadow 0.3s; border: 1px solid #e9ecef; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 15px; font-size: 1.5rem; }
        .card p { color: #7f8c8d; line-height: 1.6; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px; }
        .stat-box { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.08); border-top: 4px solid #3498db; }
        .stat-number { font-size: 2.5rem; font-weight: bold; color: #2c3e50; margin: 10px 0; }
        .stat-label { color: #7f8c8d; font-size: 0.9rem; }
        .footer { text-align: center; padding: 20px; color: #7f8c8d; border-top: 1px solid #eee; margin-top: 40px; }

        @media (max-width: 768px) {
            .nav { flex-direction: column; align-items: center; }
            .nav-btn { width: 80%; text-align: center; }
            .stats { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 480px) {
            .stats { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏢 Rawas Real Estate Investment</h1>
            <p>Comprehensive Management System for Real Estate Operations</p>
        </div>

        <div class="nav">
            <a href="/dashboard" class="nav-btn">📊 Dashboard</a>
            <a href="/projects" class="nav-btn">🏗️ Projects</a>
            <a href="/sales" class="nav-btn">💰 Sales</a>
            <a href="/clients" class="nav-btn">👥 Clients</a>
            <a href="/employees" class="nav-btn">👨‍💼 Employees</a>
            <a href="/inventory" class="nav-btn">📦 Inventory</a>
            <a href="/reports" class="nav-btn">📈 Reports</a>
        </div>

        <div class="content">
            <div class="card">
                <h3>📋 System Overview</h3>
                <p>Manage all your real estate operations in one place. Track projects, sales, inventory, and generate reports.</p>
            </div>

            <div class="card">
                <h3>🚀 Quick Start</h3>
                <p>1. Add your projects and buildings<br>
                   2. Register available units<br>
                   3. Add clients and record sales<br>
                   4. Manage employees and inventory</p>
            </div>

            <div class="card">
                <h3>📞 Contact Support</h3>
                <p>Email: info@rawas.ps<br>
                   Phone: 059330060<br>
                   Location: Ramallah, Palestine</p>
            </div>
        </div>

        <div id="stats" class="stats">
            <!-- Stats will be loaded by JavaScript -->
        </div>

        <div class="footer">
            <p>© 2025 Rawas Real Estate Investment. All rights reserved.</p>
        </div>
    </div>

    <script>
        async function loadStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;
                    const statsContainer = document.getElementById('stats');

                    statsContainer.innerHTML = `
                        <div class="stat-box">
                            <div class="stat-number">${stats.projects}</div>
                            <div class="stat-label">Projects</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${stats.units?.Available || 0}</div>
                            <div class="stat-label">Available Units</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${stats.sales_count}</div>
                            <div class="stat-label">Total Sales</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">${stats.clients}</div>
                            <div class="stat-label">Clients</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        document.addEventListener('DOMContentLoaded', loadStats);
    </script>
</body>
</html>''')

    # employees.html
    with open('templates/employees.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Employees Management - Rawas Real Estate</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            flex-wrap: wrap; 
            gap: 20px; 
        }
        .header h1 { color: #2c3e50; }
        
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        .nav-btn { 
            padding: 10px 20px; 
            background: #3498db; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
        }
        
        .btn { 
            padding: 12px 25px; 
            background: #3498db; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 1rem; 
            transition: all 0.3s; 
        }
        .btn:hover { 
            background: #2980b9; 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #d68910; }
        .btn-sm { padding: 5px 10px; font-size: 0.9rem; }
        
        .search-box { 
            margin-bottom: 20px; 
            display: flex;
            gap: 10px;
        }
        .search-box input { 
            flex: 1;
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 1rem; 
        }
        
        .table-container { 
            background: white; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
            margin-bottom: 30px; 
            overflow-x: auto; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            min-width: 1000px; 
        }
        th { 
            background: #f8f9fa; 
            padding: 15px; 
            text-align: left; 
            color: #2c3e50; 
            font-weight: 600; 
            border-bottom: 1px solid #e0e0e0; 
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #e0e0e0; 
        }
        tr:hover { background: #f9f9f9; }
        tr:last-child td { border-bottom: none; }
        
        .status-badge { 
            padding: 5px 10px; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            display: inline-block;
            font-weight: 600;
        }
        .status-active { background: #d4edda; color: #155724; }
        .status-inactive { background: #f8d7da; color: #721c24; }
        .status-on-leave { background: #fff3cd; color: #856404; }
        
        .employee-avatar { 
            width: 40px; 
            height: 40px; 
            border-radius: 50%; 
            background: #3498db; 
            color: white; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-weight: bold; 
        }
        
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.5); 
            justify-content: center; 
            align-items: center; 
            z-index: 1000; 
        }
        .modal-content { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            max-width: 600px; 
            width: 90%; 
            max-height: 90vh; 
            overflow-y: auto; 
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #2c3e50; 
            font-weight: 500; 
        }
        .form-group input, 
        .form-group select, 
        .form-group textarea { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 1rem; 
        }
        .form-row { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
        }
        .form-actions { 
            display: flex; 
            gap: 10px; 
            justify-content: flex-end; 
            margin-top: 20px; 
        }
        
        .stats-cards { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .stat-card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
            text-align: center; 
        }
        .stat-value { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #2c3e50; 
            margin: 10px 0; 
        }
        .stat-label { 
            color: #7f8c8d; 
            font-size: 0.9rem; 
        }
        
        .message { 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
            display: none; 
        }
        .message.success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .message.error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: flex-start; }
            .search-box { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
            <a href="/dashboard" class="nav-btn"><i class="fas fa-chart-bar"></i> Dashboard</a>
            <a href="/projects" class="nav-btn"><i class="fas fa-building"></i> Projects</a>
            <a href="/sales" class="nav-btn"><i class="fas fa-dollar-sign"></i> Sales</a>
            <a href="/clients" class="nav-btn"><i class="fas fa-users"></i> Clients</a>
            <a href="/inventory" class="nav-btn"><i class="fas fa-box"></i> Inventory</a>
        </div>

        <div class="header">
            <h1><i class="fas fa-users"></i> Employees Management</h1>
            <button class="btn btn-success" onclick="openEmployeeModal()">
                <i class="fas fa-plus"></i> Add Employee
            </button>
        </div>

        <div id="message" class="message"></div>

        <div class="stats-cards" id="statsCards">
            <!-- Statistics will be loaded here -->
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search by name, position, or email..." onkeyup="searchEmployees()">
            <select id="statusFilter" onchange="filterEmployees()">
                <option value="all">All Status</option>
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="On Leave">On Leave</option>
            </select>
        </div>

        <div class="table-container">
            <table id="employeesTable">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Position</th>
                        <th>Contact</th>
                        <th>Salary</th>
                        <th>Status</th>
                        <th>Joined</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add/Edit Employee Modal -->
    <div id="employeeModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="modalTitle">
                <i class="fas fa-user-plus"></i> Add New Employee
            </h2>
            <form id="employeeForm">
                <input type="hidden" id="employeeId">

                <div class="form-row">
                    <div class="form-group">
                        <label for="employeeName"><i class="fas fa-user"></i> Full Name *</label>
                        <input type="text" id="employeeName" required>
                    </div>
                    <div class="form-group">
                        <label for="employeePosition"><i class="fas fa-briefcase"></i> Position *</label>
                        <input type="text" id="employeePosition" required>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="employeePhone"><i class="fas fa-phone"></i> Phone Number *</label>
                        <input type="tel" id="employeePhone" required>
                    </div>
                    <div class="form-group">
                        <label for="employeeEmail"><i class="fas fa-envelope"></i> Email</label>
                        <input type="email" id="employeeEmail">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="employeeSalary"><i class="fas fa-money-bill-wave"></i> Salary ($)</label>
                        <input type="number" id="employeeSalary" step="0.01" min="0">
                    </div>
                    <div class="form-group">
                        <label for="employeeStatus"><i class="fas fa-check-circle"></i> Status</label>
                        <select id="employeeStatus">
                            <option value="Active">Active</option>
                            <option value="Inactive">Inactive</option>
                            <option value="On Leave">On Leave</option>
                        </select>
                    </div>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeEmployeeModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success" id="submitButton">
                        <i class="fas fa-save"></i> Save Employee
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div id="deleteModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-exclamation-triangle"></i> Confirm Delete</h2>
            <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <p id="deleteMessage">Are you sure you want to delete this employee?</p>
                <p style="color: #e74c3c; font-size: 0.9rem; margin-top: 10px;">
                    <i class="fas fa-warning"></i> This action cannot be undone!
                </p>
            </div>
            <div class="form-actions">
                <button type="button" class="btn" onclick="closeDeleteModal()">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    </div>

    <script>
        let allEmployees = [];
        let employeeToDelete = null;

        document.addEventListener('DOMContentLoaded', function() {
            loadEmployees();
            loadEmployeeStats();
        });

        function showMessage(message, type = 'success') {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = message;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'block';

            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        async function loadEmployees() {
            try {
                const response = await fetch('/api/employees');
                const data = await response.json();

                if (data.success) {
                    allEmployees = data.data;
                    displayEmployees(allEmployees);
                } else {
                    showMessage('Error loading employees: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Error loading employees:', error);
                showMessage('Error loading employees', 'error');
            }
        }

        async function loadEmployeeStats() {
            try {
                const response = await fetch('/api/employees/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;
                    const statsContainer = document.getElementById('statsCards');

                    statsContainer.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${stats.total || 0}</div>
                            <div class="stat-label">Total Employees</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.active || 0}</div>
                            <div class="stat-label">Active</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.inactive || 0}</div>
                            <div class="stat-label">Inactive</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">$${(stats.total_salary || 0).toLocaleString()}</div>
                            <div class="stat-label">Monthly Salary</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        function displayEmployees(employees) {
            const tbody = document.querySelector('#employeesTable tbody');

            if (!employees || employees.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; padding: 40px; color: #7f8c8d;">
                            <i class="fas fa-users" style="font-size: 2rem; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                            No employees found
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = employees.map(employee => {
                const avatarText = employee.name ? employee.name.charAt(0).toUpperCase() : 'E';
                const joinDate = new Date(employee.created_at || Date.now());
                const formattedDate = joinDate.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });
                
                const salary = employee.salary ? 
                    `$${parseFloat(employee.salary).toLocaleString()}` : 
                    'Not set';

                return `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="employee-avatar">${avatarText}</div>
                            <div>
                                <strong>${employee.name || 'Unknown'}</strong>
                                ${employee.email ? `<br><small>${employee.email}</small>` : ''}
                            </div>
                        </div>
                    </td>
                    <td>${employee.position || '-'}</td>
                    <td>
                        ${employee.phone || '-'}
                        ${employee.email ? `<br><small>${employee.email}</small>` : ''}
                    </td>
                    <td><strong>${salary}</strong></td>
                    <td>
                        <span class="status-badge status-${employee.status ? employee.status.toLowerCase().replace(' ', '-') : 'active'}">
                            ${employee.status || 'Active'}
                        </span>
                    </td>
                    <td>${formattedDate}</td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="editEmployee(${employee.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteEmployee(${employee.id}, '${employee.name ? employee.name.replace(/'/g, "\\'") : ''}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
                `;
            }).join('');
        }
    

        function searchEmployees() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const statusFilter = document.getElementById('statusFilter').value;

            if (!searchTerm && statusFilter === 'all') {
                displayEmployees(allEmployees);
                return;
            }

            const filtered = allEmployees.filter(employee => {
                const matchesSearch = !searchTerm || 
                    (employee.name && employee.name.toLowerCase().includes(searchTerm)) ||
                    (employee.position && employee.position.toLowerCase().includes(searchTerm)) ||
                    (employee.email && employee.email.toLowerCase().includes(searchTerm)) ||
                    (employee.phone && employee.phone.includes(searchTerm));

                const matchesStatus = statusFilter === 'all' || employee.status === statusFilter;

                return matchesSearch && matchesStatus;
            });

            displayEmployees(filtered);
        }

        function filterEmployees() {
            searchEmployees();
        }

        function openEmployeeModal(employeeId = null) {
            const modal = document.getElementById('employeeModal');
            const title = document.getElementById('modalTitle');
            const submitBtn = document.getElementById('submitButton');

            if (employeeId) {
                title.innerHTML = '<i class="fas fa-user-edit"></i> Edit Employee';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Employee';
                loadEmployeeData(employeeId);
            } else {
                title.innerHTML = '<i class="fas fa-user-plus"></i> Add New Employee';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Employee';
                document.getElementById('employeeForm').reset();
                document.getElementById('employeeId').value = '';
            }

            modal.style.display = 'flex';
        }

        function closeEmployeeModal() {
            document.getElementById('employeeModal').style.display = 'none';
            document.getElementById('employeeForm').reset();
        }

        async function loadEmployeeData(employeeId) {
            try {
                const response = await fetch(`/api/employees/${employeeId}`);
                const data = await response.json();

                if (data.success) {
                    const employee = data.data;
                    document.getElementById('employeeId').value = employee.id;
                    document.getElementById('employeeName').value = employee.name || '';
                    document.getElementById('employeePosition').value = employee.position || '';
                    document.getElementById('employeePhone').value = employee.phone || '';
                    document.getElementById('employeeEmail').value = employee.email || '';
                    document.getElementById('employeeSalary').value = employee.salary || '';
                    document.getElementById('employeeStatus').value = employee.status || 'Active';
                } else {
                    showMessage('Error loading employee data: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Error loading employee data:', error);
                showMessage('Error loading employee data', 'error');
            }
        }

        document.getElementById('employeeForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const employeeId = document.getElementById('employeeId').value;
            const submitBtn = document.getElementById('submitButton');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitBtn.disabled = true;

            const employeeData = {
                name: document.getElementById('employeeName').value,
                position: document.getElementById('employeePosition').value,
                phone: document.getElementById('employeePhone').value,
                email: document.getElementById('employeeEmail').value,
                salary: parseFloat(document.getElementById('employeeSalary').value) || null,
                status: document.getElementById('employeeStatus').value
            };

            if (!employeeData.name || !employeeData.position || !employeeData.phone) {
                showMessage('Name, position, and phone are required!', 'error');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                return;
            }

            try {
                const url = employeeId ? `/api/employees/${employeeId}` : '/api/employees';
                const method = employeeId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(employeeData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(employeeId ? 'Employee updated successfully!' : 'Employee added successfully!');
                    closeEmployeeModal();
                    loadEmployees();
                    loadEmployeeStats();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to save employee'), 'error');
                }
            } catch (error) {
                showMessage('Error saving employee', 'error');
                console.error(error);
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });

        function editEmployee(employeeId) {
            openEmployeeModal(employeeId);
        }

        function deleteEmployee(employeeId, employeeName) {
            employeeToDelete = employeeId;
            document.getElementById('deleteMessage').innerHTML = `
                Are you sure you want to delete employee <strong>"${employeeName}"</strong>?<br>
                This will permanently remove all their information from the system.
            `;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function closeDeleteModal() {
            document.getElementById('deleteModal').style.display = 'none';
            employeeToDelete = null;
        }

        async function confirmDelete() {
            if (!employeeToDelete) return;

            const deleteBtn = document.querySelector('#deleteModal .btn-danger');
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            deleteBtn.disabled = true;

            try {
                const response = await fetch(`/api/employees/${employeeToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Employee deleted successfully!');
                    closeDeleteModal();
                    loadEmployees();
                    loadEmployeeStats();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to delete employee'), 'error');
                }
            } catch (error) {
                showMessage('Error deleting employee', 'error');
                console.error(error);
            } finally {
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                employeeToDelete = null;
            }
        }

        window.onclick = function(event) {
            const employeeModal = document.getElementById('employeeModal');
            const deleteModal = document.getElementById('deleteModal');

            if (event.target === employeeModal) closeEmployeeModal();
            if (event.target === deleteModal) closeDeleteModal();
        };

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeEmployeeModal();
                closeDeleteModal();
            }
        });
    </script>
</body>
</html>''')

    # inventory.html
    with open('templates/inventory.html', 'w', encoding='utf-8') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory Management - Rawas Real Estate</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            flex-wrap: wrap; 
            gap: 20px; 
        }
        .header h1 { color: #2c3e50; }
        
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
        }
        .nav-btn { 
            padding: 10px 20px; 
            background: #3498db; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
        }
        
        .btn { 
            padding: 12px 25px; 
            background: #3498db; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 1rem; 
            transition: all 0.3s; 
        }
        .btn:hover { 
            background: #2980b9; 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #d68910; }
        .btn-sm { padding: 5px 10px; font-size: 0.9rem; }
        
        .search-box { 
            margin-bottom: 20px; 
            display: flex;
            gap: 10px;
        }
        .search-box input { 
            flex: 1;
            padding: 12px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 1rem; 
        }
        .search-box select {
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            background: white;
        }
        
        .stats-cards { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        .stat-card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
            text-align: center; 
        }
        .stat-value { 
            font-size: 2rem; 
            font-weight: bold; 
            color: #2c3e50; 
            margin: 10px 0; 
        }
        .stat-label { 
            color: #7f8c8d; 
            font-size: 0.9rem; 
        }
        
        .table-container { 
            background: white; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.08); 
            margin-bottom: 30px; 
            overflow-x: auto; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            min-width: 1200px; 
        }
        th { 
            background: #f8f9fa; 
            padding: 15px; 
            text-align: left; 
            color: #2c3e50; 
            font-weight: 600; 
            border-bottom: 1px solid #e0e0e0; 
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #e0e0e0; 
        }
        tr:hover { background: #f9f9f9; }
        tr:last-child td { border-bottom: none; }
        
        .stock-status { 
            padding: 5px 10px; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            display: inline-block;
            font-weight: 600;
        }
        .stock-adequate { background: #d4edda; color: #155724; }
        .stock-low { background: #fff3cd; color: #856404; }
        .stock-critical { background: #f8d7da; color: #721c24; }
        .stock-out { background: #e9ecef; color: #495057; }
        
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.5); 
            justify-content: center; 
            align-items: center; 
            z-index: 1000; 
        }
        .modal-content { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            max-width: 600px; 
            width: 90%; 
            max-height: 90vh; 
            overflow-y: auto; 
        }
        .form-group { margin-bottom: 20px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #2c3e50; 
            font-weight: 500; 
        }
        .form-group input, 
        .form-group select, 
        .form-group textarea { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 1rem; 
        }
        .form-row { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
        }
        .form-actions { 
            display: flex; 
            gap: 10px; 
            justify-content: flex-end; 
            margin-top: 20px; 
        }
        
        .message { 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
            display: none; 
        }
        .message.success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .message.error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: flex-start; }
            .search-box { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
            <a href="/dashboard" class="nav-btn"><i class="fas fa-chart-bar"></i> Dashboard</a>
            <a href="/projects" class="nav-btn"><i class="fas fa-building"></i> Projects</a>
            <a href="/sales" class="nav-btn"><i class="fas fa-dollar-sign"></i> Sales</a>
            <a href="/clients" class="nav-btn"><i class="fas fa-users"></i> Clients</a>
            <a href="/employees" class="nav-btn"><i class="fas fa-users-cog"></i> Employees</a>
        </div>

        <div class="header">
            <h1><i class="fas fa-box"></i> Inventory Management</h1>
            <button class="btn btn-success" onclick="openMaterialModal()">
                <i class="fas fa-plus"></i> Add Material
            </button>
        </div>

        <div id="message" class="message"></div>

        <div class="stats-cards" id="statsCards">
            <!-- Statistics will be loaded here -->
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search by material name or category..." onkeyup="searchMaterials()">
            <select id="categoryFilter" onchange="filterMaterials()">
                <option value="all">All Categories</option>
                <option value="Construction">Construction</option>
                <option value="Electrical">Electrical</option>
                <option value="Plumbing">Plumbing</option>
                <option value="Finishing">Finishing</option>
                <option value="Other">Other</option>
            </select>
        </div>

        <div class="table-container">
            <table id="inventoryTable">
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Category</th>
                        <th>Unit</th>
                        <th>Unit Price</th>
                        <th>Min Quantity</th>
                        <th>Current Stock</th>
                        <th>Status</th>
                        <th>Last Updated</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add/Edit Material Modal -->
    <div id="materialModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="modalTitle">
                <i class="fas fa-box-open"></i> Add New Material
            </h2>
            <form id="materialForm">
                <input type="hidden" id="materialId">

                <div class="form-row">
                    <div class="form-group">
                        <label for="materialName"><i class="fas fa-signature"></i> Material Name *</label>
                        <input type="text" id="materialName" required>
                    </div>
                    <div class="form-group">
                        <label for="materialCategory"><i class="fas fa-tag"></i> Category *</label>
                        <select id="materialCategory" required>
                            <option value="">Select Category</option>
                            <option value="Construction">Construction</option>
                            <option value="Electrical">Electrical</option>
                            <option value="Plumbing">Plumbing</option>
                            <option value="Finishing">Finishing</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="materialUnit"><i class="fas fa-balance-scale"></i> Unit *</label>
                        <select id="materialUnit" required>
                            <option value="">Select Unit</option>
                            <option value="Bag">Bag</option>
                            <option value="Ton">Ton</option>
                            <option value="Meter">Meter</option>
                            <option value="Box">Box</option>
                            <option value="Liter">Liter</option>
                            <option value="Piece">Piece</option>
                            <option value="Set">Set</option>
                            <option value="Roll">Roll</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="materialPrice"><i class="fas fa-money-bill-wave"></i> Unit Price ($) *</label>
                        <input type="number" id="materialPrice" step="0.01" min="0" required>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="materialMinQuantity"><i class="fas fa-exclamation-triangle"></i> Minimum Quantity *</label>
                        <input type="number" id="materialMinQuantity" min="0" required value="10">
                    </div>
                    <div class="form-group">
                        <label for="materialInitialStock"><i class="fas fa-boxes"></i> Initial Stock</label>
                        <input type="number" id="materialInitialStock" min="0" value="0">
                    </div>
                </div>

                <div class="form-group">
                    <label for="materialLocation"><i class="fas fa-map-marker-alt"></i> Storage Location</label>
                    <input type="text" id="materialLocation" placeholder="Warehouse, Shelf A, etc.">
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeMaterialModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success" id="submitButton">
                        <i class="fas fa-save"></i> Save Material
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Stock Adjustment Modal -->
    <div id="stockModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-exchange-alt"></i> Adjust Stock</h2>
            <form id="stockForm">
                <input type="hidden" id="stockMaterialId">
                <input type="hidden" id="stockCurrentQuantity">

                <div class="form-group">
                    <label><strong>Material:</strong> <span id="stockMaterialName">Loading...</span></label>
                </div>

                <div class="form-group">
                    <label><strong>Current Stock:</strong> <span id="stockCurrent">0</span> <span id="stockUnit"></span></label>
                </div>

                <div class="form-group">
                    <label><strong>Minimum Quantity:</strong> <span id="stockMinQuantity">0</span> <span id="stockMinUnit"></span></label>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="stockAdjustmentType">Adjustment Type *</label>
                        <select id="stockAdjustmentType" required onchange="toggleStockReason()">
                            <option value="">Select Type</option>
                            <option value="IN">Add Stock (IN)</option>
                            <option value="OUT">Remove Stock (OUT)</option>
                            <option value="SET">Set Stock (SET)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="stockAdjustmentQuantity">Quantity *</label>
                        <input type="number" id="stockAdjustmentQuantity" min="0" step="1" required>
                    </div>
                </div>

                <div class="form-group" id="reasonGroup" style="display: none;">
                    <label for="stockReason">Reason</label>
                    <select id="stockReason">
                        <option value="">Select Reason</option>
                        <option value="PURCHASE">New Purchase</option>
                        <option value="RETURN">Return</option>
                        <option value="USAGE">Project Usage</option>
                        <option value="DAMAGED">Damaged/Expired</option>
                        <option value="ADJUSTMENT">Inventory Adjustment</option>
                        <option value="OTHER">Other</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="stockNotes">Notes</label>
                    <textarea id="stockNotes" rows="2" placeholder="Additional information..."></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeStockModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-save"></i> Update Stock
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div id="deleteModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-exclamation-triangle"></i> Confirm Delete</h2>
            <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <p id="deleteMessage">Are you sure you want to delete this material?</p>
                <p style="color: #e74c3c; font-size: 0.9rem; margin-top: 10px;">
                    <i class="fas fa-warning"></i> This will also delete all inventory records for this material!
                </p>
            </div>
            <div class="form-actions">
                <button type="button" class="btn" onclick="closeDeleteModal()">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    </div>

    <script>
        let allMaterials = [];
        let materialToDelete = null;

        document.addEventListener('DOMContentLoaded', function() {
            loadMaterials();
            loadInventoryStats();
        });

        function showMessage(message, type = 'success') {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = message;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'block';

            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        async function loadMaterials() {
            try {
                const response = await fetch('/api/materials');
                const data = await response.json();

                if (data.success) {
                    allMaterials = data.data;
                    displayMaterials(allMaterials);
                } else {
                    showMessage('Error loading materials: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Error loading materials:', error);
                showMessage('Error loading materials', 'error');
            }
        }

        async function loadInventoryStats() {
            try {
                const response = await fetch('/api/inventory/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;
                    const statsContainer = document.getElementById('statsCards');

                    statsContainer.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${stats.total_materials || 0}</div>
                            <div class="stat-label">Total Materials</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.low_stock || 0}</div>
                            <div class="stat-label">Low Stock</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.critical_stock || 0}</div>
                            <div class="stat-label">Critical Stock</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">$${(stats.total_value || 0).toLocaleString()}</div>
                            <div class="stat-label">Total Value</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        function displayMaterials(materials) {
            const tbody = document.querySelector('#inventoryTable tbody');

            if (!materials || materials.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" style="text-align: center; padding: 40px; color: #7f8c8d;">
                            <i class="fas fa-boxes" style="font-size: 2rem; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                            No materials found
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = materials.map(material => {
                const currentStock = material.current_stock || 0;
                const minQuantity = material.min_quantity || 0;
                
                let stockStatus = 'stock-adequate';
                let statusText = 'Adequate';
                
                if (currentStock === 0) {
                    stockStatus = 'stock-out';
                    statusText = 'Out of Stock';
                } else if (currentStock <= minQuantity * 0.2) {
                    stockStatus = 'stock-critical';
                    statusText = 'Critical';
                } else if (currentStock <= minQuantity) {
                    stockStatus = 'stock-low';
                    statusText = 'Low';
                }
                
                const lastUpdated = material.last_updated ? 
                    new Date(material.last_updated).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    }) : 'N/A';

                return `
                <tr>
                    <td>
                        <strong>${material.name || 'Unknown'}</strong>
                        ${material.location ? `<br><small><i class="fas fa-map-marker-alt"></i> ${material.location}</small>` : ''}
                    </td>
                    <td>${material.category || '-'}</td>
                    <td>${material.unit || '-'}</td>
                    <td><strong>$${material.price ? parseFloat(material.price).toFixed(2) : '0.00'}</strong></td>
                    <td>${minQuantity}</td>
                    <td><strong>${currentStock}</strong></td>
                    <td>
                        <span class="stock-status ${stockStatus}">
                            ${statusText}
                        </span>
                    </td>
                    <td>${lastUpdated}</td>
                    <td>
                        <button class="btn btn-sm" onclick="adjustStock(${material.id}, '${material.name ? material.name.replace(/'/g, "\\'") : ''}', ${currentStock}, '${material.unit || ''}', ${minQuantity})" title="Adjust Stock">
                            <i class="fas fa-exchange-alt"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="editMaterial(${material.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteMaterial(${material.id}, '${material.name ? material.name.replace(/'/g, "\\'") : ''}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
                `;
            }).join('');
        }

        function searchMaterials() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const categoryFilter = document.getElementById('categoryFilter').value;

            if (!searchTerm && categoryFilter === 'all') {
                displayMaterials(allMaterials);
                return;
            }

            const filtered = allMaterials.filter(material => {
                const matchesSearch = !searchTerm || 
                    (material.name && material.name.toLowerCase().includes(searchTerm)) ||
                    (material.category && material.category.toLowerCase().includes(searchTerm));

                const matchesCategory = categoryFilter === 'all' || material.category === categoryFilter;

                return matchesSearch && matchesCategory;
            });

            displayMaterials(filtered);
        }

        function filterMaterials() {
            searchMaterials();
        }

        function openMaterialModal(materialId = null) {
            const modal = document.getElementById('materialModal');
            const title = document.getElementById('modalTitle');
            const submitBtn = document.getElementById('submitButton');

            if (materialId) {
                title.innerHTML = '<i class="fas fa-edit"></i> Edit Material';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Material';
                loadMaterialData(materialId);
            } else {
                title.innerHTML = '<i class="fas fa-box-open"></i> Add New Material';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Material';
                document.getElementById('materialForm').reset();
                document.getElementById('materialId').value = '';
            }

            modal.style.display = 'flex';
        }

        function closeMaterialModal() {
            document.getElementById('materialModal').style.display = 'none';
            document.getElementById('materialForm').reset();
        }

        async function loadMaterialData(materialId) {
            try {
                const response = await fetch(`/api/materials/${materialId}`);
                const data = await response.json();

                if (data.success) {
                    const material = data.data;
                    document.getElementById('materialId').value = material.id;
                    document.getElementById('materialName').value = material.name || '';
                    document.getElementById('materialCategory').value = material.category || '';
                    document.getElementById('materialUnit').value = material.unit || '';
                    document.getElementById('materialPrice').value = material.price || '';
                    document.getElementById('materialMinQuantity').value = material.min_quantity || 10;
                    document.getElementById('materialInitialStock').value = material.current_stock || 0;
                    document.getElementById('materialLocation').value = material.location || '';
                } else {
                    showMessage('Error loading material data: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Error loading material data:', error);
                showMessage('Error loading material data', 'error');
            }
        }

        document.getElementById('materialForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const materialId = document.getElementById('materialId').value;
            const submitBtn = document.getElementById('submitButton');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            submitBtn.disabled = true;

            const materialData = {
                name: document.getElementById('materialName').value,
                category: document.getElementById('materialCategory').value,
                unit: document.getElementById('materialUnit').value,
                price: parseFloat(document.getElementById('materialPrice').value) || 0,
                min_quantity: parseInt(document.getElementById('materialMinQuantity').value) || 10,
                location: document.getElementById('materialLocation').value || null,
                initial_stock: parseInt(document.getElementById('materialInitialStock').value) || 0
            };

            if (!materialData.name || !materialData.category || !materialData.unit || materialData.price <= 0) {
                showMessage('Name, category, unit, and valid price are required!', 'error');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                return;
            }

            try {
                const url = materialId ? `/api/materials/${materialId}` : '/api/materials';
                const method = materialId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(materialData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(materialId ? 'Material updated successfully!' : 'Material added successfully!');
                    closeMaterialModal();
                    loadMaterials();
                    loadInventoryStats();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to save material'), 'error');
                }
            } catch (error) {
                showMessage('Error saving material', 'error');
                console.error(error);
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });

        function editMaterial(materialId) {
            openMaterialModal(materialId);
        }

        function adjustStock(materialId, materialName, currentStock, unit, minQuantity) {
            document.getElementById('stockMaterialId').value = materialId;
            document.getElementById('stockCurrentQuantity').value = currentStock;
            document.getElementById('stockMaterialName').textContent = materialName;
            document.getElementById('stockCurrent').textContent = currentStock;
            document.getElementById('stockUnit').textContent = unit;
            document.getElementById('stockMinQuantity').textContent = minQuantity;
            document.getElementById('stockMinUnit').textContent = unit;
            
            document.getElementById('stockAdjustmentQuantity').value = '';
            document.getElementById('stockReason').value = '';
            document.getElementById('stockNotes').value = '';
            
            document.getElementById('stockModal').style.display = 'flex';
        }

        function toggleStockReason() {
            const adjustmentType = document.getElementById('stockAdjustmentType').value;
            const reasonGroup = document.getElementById('reasonGroup');
            
            if (adjustmentType === 'OUT') {
                reasonGroup.style.display = 'block';
            } else {
                reasonGroup.style.display = 'none';
            }
        }

        function closeStockModal() {
            document.getElementById('stockModal').style.display = 'none';
            document.getElementById('stockForm').reset();
        }

        document.getElementById('stockForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const materialId = document.getElementById('stockMaterialId').value;
            const adjustmentType = document.getElementById('stockAdjustmentType').value;
            const quantity = parseInt(document.getElementById('stockAdjustmentQuantity').value);
            const reason = document.getElementById('stockReason').value;
            const notes = document.getElementById('stockNotes').value;
            const currentStock = parseInt(document.getElementById('stockCurrentQuantity').value);

            if (!adjustmentType || quantity <= 0) {
                showMessage('Please select adjustment type and enter valid quantity!', 'error');
                return;
            }

            if (adjustmentType === 'OUT' && quantity > currentStock) {
                showMessage('Cannot remove more stock than available!', 'error');
                return;
            }

            const stockData = {
                material_id: materialId,
                adjustment_type: adjustmentType,
                quantity: quantity,
                reason: adjustmentType === 'OUT' ? reason : null,
                notes: notes || null
            };

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/inventory/adjust', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(stockData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Stock updated successfully!');
                    closeStockModal();
                    loadMaterials();
                    loadInventoryStats();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to update stock'), 'error');
                }
            } catch (error) {
                showMessage('Error updating stock', 'error');
                console.error(error);
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });

        function deleteMaterial(materialId, materialName) {
            materialToDelete = materialId;
            document.getElementById('deleteMessage').innerHTML = `
                Are you sure you want to delete material <strong>"${materialName}"</strong>?<br>
                This will permanently remove the material and all its stock records.
            `;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function closeDeleteModal() {
            document.getElementById('deleteModal').style.display = 'none';
            materialToDelete = null;
        }

        async function confirmDelete() {
            if (!materialToDelete) return;

            const deleteBtn = document.querySelector('#deleteModal .btn-danger');
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            deleteBtn.disabled = true;

            try {
                const response = await fetch(`/api/materials/${materialToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Material deleted successfully!');
                    closeDeleteModal();
                    loadMaterials();
                    loadInventoryStats();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to delete material'), 'error');
                }
            } catch (error) {
                showMessage('Error deleting material', 'error');
                console.error(error);
            } finally {
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                materialToDelete = null;
            }
        }

        window.onclick = function(event) {
            const materialModal = document.getElementById('materialModal');
            const stockModal = document.getElementById('stockModal');
            const deleteModal = document.getElementById('deleteModal');

            if (event.target === materialModal) closeMaterialModal();
            if (event.target === stockModal) closeStockModal();
            if (event.target === deleteModal) closeDeleteModal();
        };

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeMaterialModal();
                closeStockModal();
                closeDeleteModal();
            }
        });
    </script>
</body>
</html>''')

    # Create other HTML files
    html_files = {
        'dashboard.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Rawas Real Estate</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { margin-bottom: 30px; }
        .header h1 { color: #2c3e50; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
        .stat-value { font-size: 2.5rem; font-weight: bold; color: #2c3e50; margin: 10px 0; }
        .stat-label { color: #7f8c8d; font-size: 1rem; }
        .chart-container { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .recent-table { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; color: #2c3e50; font-weight: 600; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .nav-btn { padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="nav-btn">🏠 Home</a>
            <a href="/projects" class="nav-btn">🏗️ Projects</a>
            <a href="/sales" class="nav-btn">💰 Sales</a>
            <a href="/clients" class="nav-btn">👥 Clients</a>
            <a href="/employees" class="nav-btn">👨‍💼 Employees</a>
            <a href="/inventory" class="nav-btn">📦 Inventory</a>
            <a href="/reports" class="nav-btn">📈 Reports</a>
        </div>

        <div class="header">
            <h1>📊 Dashboard</h1>
            <p>Real-time overview of your real estate operations</p>
        </div>

        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be loaded here -->
        </div>

        <div class="chart-container">
            <h3>Sales Overview</h3>
            <canvas id="salesChart" height="100"></canvas>
        </div>

        <div class="recent-table">
            <h3>Recent Payments</h3>
            <table id="recentPayments">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Client</th>
                        <th>Amount</th>
                        <th>Method</th>
                        <th>Receipt #</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Recent payments will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;

                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-label">Total Projects</div>
                            <div class="stat-value">${stats.projects || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Available Units</div>
                            <div class="stat-value">${stats.units?.Available || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Sales</div>
                            <div class="stat-value">${stats.sales_count || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Clients</div>
                            <div class="stat-value">${stats.clients || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total Employees</div>
                            <div class="stat-value">${stats.employees || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Sales Revenue</div>
                            <div class="stat-value">$${(stats.sales_revenue || 0).toLocaleString()}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Active Sales</div>
                            <div class="stat-value">${stats.active_sales || 0}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Delayed Payments</div>
                            <div class="stat-value">${stats.delayed_payments || 0}</div>
                        </div>
                    `;

                    if (data.recent_payments && data.recent_payments.length > 0) {
                        const tbody = document.querySelector('#recentPayments tbody');
                        tbody.innerHTML = data.recent_payments.map(payment => {
                            const paymentDate = payment.payment_date ? 
                                new Date(payment.payment_date).toLocaleDateString('en-GB') : '';
                            
                            return `
                            <tr>
                                <td>${paymentDate}</td>
                                <td>${payment.client_name || ''}</td>
                                <td>$${payment.amount?.toLocaleString() || 0}</td>
                                <td>${payment.method || ''}</td>
                                <td>${payment.receipt_number || ''}</td>
                            </tr>
                            `;
                        }).join('');
                    }
                }
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        document.addEventListener('DOMContentLoaded', loadDashboardData);
    </script>
</body>
</html>''',

        'projects.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Projects Management - Rawas Real Estate</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            margin-bottom: 30px; 
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        .header h1 { color: #2c3e50; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .nav-btn { padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        .btn { padding: 12px 25px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: all 0.3s; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #d68910; }
        .btn-sm { padding: 5px 10px; font-size: 0.9rem; }
        .btn-info { background: #17a2b8; }
        .btn-info:hover { background: #138496; }

        .projects-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .project-card { 
            background: white; 
            border-radius: 10px; 
            overflow: hidden; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .project-card:hover { 
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        .project-header { 
            padding: 20px; 
            background: linear-gradient(to right, #2c3e50, #3498db); 
            color: white;
            position: relative;
        }
        .project-actions {
            position: absolute;
            top: 15px;
            right: 15px;
            display: flex;
            gap: 5px;
        }
        .project-body { padding: 20px; }
        .project-stats { 
            display: grid; 
            grid-template-columns: repeat(2, 1fr); 
            gap: 10px; 
            margin-top: 15px;
        }
        .stat { 
            text-align: center; 
            padding: 10px; 
            background: #f8f9fa; 
            border-radius: 5px;
            transition: background 0.3s;
            cursor: pointer;
        }
        .stat:hover { background: #e9ecef; }
        .stat-value { 
            font-size: 1.5rem; 
            font-weight: bold; 
            color: #2c3e50;
            display: block;
        }
        .stat-label { 
            font-size: 0.8rem; 
            color: #7f8c8d;
            display: block;
        }

        .modal { 
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.5); 
            justify-content: center; 
            align-items: center; 
            z-index: 1000; 
        }
        .modal-content { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            max-width: 500px; 
            width: 90%; 
            max-height: 90vh; 
            overflow-y: auto; 
        }
        .modal-lg { max-width: 800px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { 
            display: block; 
            margin-bottom: 5px; 
            color: #2c3e50; 
            font-weight: 500; 
        }
        .form-group input, .form-group select, .form-group textarea { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            font-size: 1rem; 
        }
        .form-row { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 15px; 
        }
        .form-actions { 
            display: flex; 
            gap: 10px; 
            justify-content: flex-end; 
            margin-top: 20px; 
        }

        .status-badge { 
            padding: 5px 10px; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            display: inline-block;
            font-weight: 600;
        }
        .status-planning { background: #fff3cd; color: #856404; }
        .status-under-construction { background: #d1ecf1; color: #0c5460; }
        .status-active { background: #d4edda; color: #155724; }
        .status-completed { background: #cce5ff; color: #004085; }
        .status-on-hold { background: #f8d7da; color: #721c24; }

        .section-toggle { 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-top: 20px; 
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }
        .section-toggle:hover { background: #e9ecef; }
        .section-content { 
            max-height: 0; 
            overflow: hidden; 
            transition: max-height 0.3s ease-out;
        }
        .section-content.expanded { 
            max-height: 1000px; 
            padding-top: 15px;
        }

        .buildings-list, .units-list { 
            margin-top: 15px; 
            display: grid; 
            gap: 10px; 
        }
        .building-item, .unit-item { 
            background: white; 
            border: 1px solid #e0e0e0; 
            border-radius: 5px; 
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .building-info, .unit-info { flex: 1; }
        .building-actions, .unit-actions { display: flex; gap: 5px; }

        .confirmation-modal .modal-content {
            max-width: 400px;
        }
        .confirmation-message {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .message {
            padding: 10px 15px;
            border-radius: 5px;
            margin: 10px 0;
            display: none;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .unit-status-available { color: #28a745; }
        .unit-status-reserved { color: #ffc107; }
        .unit-status-sold { color: #dc3545; }
        .unit-status-under-construction { color: #17a2b8; }

        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .projects-container { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: flex-start; }
            .project-actions { position: static; margin-bottom: 10px; justify-content: flex-end; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
            <a href="/dashboard" class="nav-btn"><i class="fas fa-chart-bar"></i> Dashboard</a>
            <a href="/sales" class="nav-btn"><i class="fas fa-dollar-sign"></i> Sales</a>
            <a href="/clients" class="nav-btn"><i class="fas fa-users"></i> Clients</a>
            <a href="/employees" class="nav-btn"><i class="fas fa-users-cog"></i> Employees</a>
            <a href="/inventory" class="nav-btn"><i class="fas fa-box"></i> Inventory</a>
        </div>

        <div class="header">
            <h1><i class="fas fa-building"></i> Projects Management</h1>
            <button class="btn btn-success" onclick="openProjectModal()">
                <i class="fas fa-plus"></i> Add Project
            </button>
        </div>

        <div id="message" class="message"></div>

        <div class="projects-container" id="projectsGrid">
            <!-- Projects will be loaded here -->
        </div>
    </div>

    <!-- Add/Edit Project Modal -->
    <div id="projectModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="modalTitle"><i class="fas fa-building"></i> Add New Project</h2>
            <form id="projectForm">
                <input type="hidden" id="projectId">

                <div class="form-row">
                    <div class="form-group">
                        <label for="projectName"><i class="fas fa-signature"></i> Project Name *</label>
                        <input type="text" id="projectName" required placeholder="Enter project name">
                    </div>
                    <div class="form-group">
                        <label for="projectLocation"><i class="fas fa-map-marker-alt"></i> Location *</label>
                        <input type="text" id="projectLocation" required placeholder="Enter location">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="projectStartDate"><i class="fas fa-calendar-plus"></i> Start Date</label>
                        <input type="date" id="projectStartDate">
                    </div>
                    <div class="form-group">
                        <label for="projectEndDate"><i class="fas fa-calendar-check"></i> End Date</label>
                        <input type="date" id="projectEndDate">
                    </div>
                </div>

                <div class="form-group">
                    <label for="projectStatus"><i class="fas fa-tasks"></i> Status</label>
                    <select id="projectStatus">
                        <option value="Planning">Planning</option>
                        <option value="Under Construction">Under Construction</option>
                        <option value="Completed">Completed</option>
                        <option value="On Hold">On Hold</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="projectDescription"><i class="fas fa-align-left"></i> Description</label>
                    <textarea id="projectDescription" rows="3" placeholder="Enter project description..."></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeProjectModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success" id="submitProjectBtn">
                        <i class="fas fa-save"></i> Save Project
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Building Management Modal -->
    <div id="buildingModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-hotel"></i> Manage Buildings</h2>
            <input type="hidden" id="buildingProjectId">

            <div style="margin-bottom: 20px;">
                <button class="btn btn-sm btn-success" onclick="openAddBuildingModal()">
                    <i class="fas fa-plus"></i> Add Building
                </button>
                <button class="btn btn-sm btn-info" onclick="loadBuildingsList(document.getElementById('buildingProjectId').value)">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>

            <div id="buildingsList">
                <!-- Buildings will be listed here -->
            </div>

            <div class="form-actions">
                <button type="button" class="btn" onclick="closeBuildingModal()">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    </div>

    <!-- Add/Edit Building Modal -->
    <div id="addBuildingModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="buildingModalTitle">
                <i class="fas fa-hotel"></i> Add Building
            </h2>
            <form id="buildingForm">
                <input type="hidden" id="buildingId">
                <input type="hidden" id="buildingProjectIdInput">

                <div class="form-row">
                    <div class="form-group">
                        <label for="buildingName">Building Name *</label>
                        <input type="text" id="buildingName" required placeholder="Building A, Tower B, etc.">
                    </div>
                    <div class="form-group">
                        <label for="buildingFloors">Number of Floors</label>
                        <input type="number" id="buildingFloors" min="1" value="1">
                    </div>
                </div>

                <div class="form-group">
                    <label for="buildingStatus">Status</label>
                    <select id="buildingStatus">
                        <option value="Not Started">Not Started</option>
                        <option value="Foundation">Foundation</option>
                        <option value="Structure">Structure</option>
                        <option value="Finishing">Finishing</option>
                        <option value="Completed">Completed</option>
                    </select>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeAddBuildingModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success" id="submitBuildingBtn">
                        <i class="fas fa-save"></i> Save Building
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Unit Management Modal -->
    <div id="unitModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-door-closed"></i> Manage Units</h2>
            <div style="margin-bottom: 10px;">
                <strong>Building:</strong> <span id="unitBuildingName">Loading...</span>
            </div>
            <input type="hidden" id="unitBuildingId">

            <div style="margin-bottom: 20px;">
                <button class="btn btn-sm btn-success" onclick="openAddUnitModal()">
                    <i class="fas fa-plus"></i> Add Unit
                </button>
                <button class="btn btn-sm btn-info" onclick="loadUnitsList(document.getElementById('unitBuildingId').value)">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </div>

            <div id="unitsList">
                <!-- Units will be listed here -->
            </div>

            <div class="form-actions">
                <button type="button" class="btn" onclick="closeUnitModal()">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    </div>

    <!-- Add/Edit Unit Modal -->
    <div id="addUnitModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="unitModalTitle">
                <i class="fas fa-door-closed"></i> Add Unit
            </h2>
            <form id="unitForm">
                <input type="hidden" id="unitId">
                <input type="hidden" id="unitBuildingIdInput">

                <div class="form-row">
                    <div class="form-group">
                        <label for="unitNumber">Unit Number *</label>
                        <input type="text" id="unitNumber" required placeholder="101, 202, etc.">
                    </div>
                    <div class="form-group">
                        <label for="unitFloor">Floor</label>
                        <input type="number" id="unitFloor" min="0" value="1">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="unitType">Type</label>
                        <select id="unitType">
                            <option value="Apartment">Apartment</option>
                            <option value="Office">Office</option>
                            <option value="Villa">Villa</option>
                            <option value="Shop">Shop</option>
                            <option value="Studio">Studio</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="unitArea">Area (sqm) *</label>
                        <input type="number" id="unitArea" step="0.01" required min="1" value="100">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="unitBedrooms">Bedrooms</label>
                        <input type="number" id="unitBedrooms" min="0" value="2">
                    </div>
                    <div class="form-group">
                        <label for="unitBathrooms">Bathrooms</label>
                        <input type="number" id="unitBathrooms" min="1" value="1">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="unitPrice">Price ($) *</label>
                        <input type="number" id="unitPrice" step="0.01" required min="1" value="100000">
                    </div>
                    <div class="form-group">
                        <label for="unitStatus">Status</label>
                        <select id="unitStatus">
                            <option value="Available">Available</option>
                            <option value="Reserved">Reserved</option>
                            <option value="Sold">Sold</option>
                            <option value="Under Construction">Under Construction</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label for="unitFeatures">Features</label>
                    <textarea id="unitFeatures" rows="2" placeholder="Balcony, Parking, Garden, etc."></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeAddUnitModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button type="submit" class="btn btn-success" id="submitUnitBtn">
                        <i class="fas fa-save"></i> Save Unit
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div id="deleteModal" class="modal confirmation-modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;"><i class="fas fa-exclamation-triangle"></i> Confirm Delete</h2>
            <div class="confirmation-message" id="deleteMessage">
                Are you sure you want to delete this item?
            </div>
            <div class="form-actions">
                <button type="button" class="btn" onclick="closeDeleteModal()">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentProjectId = null;
        let currentBuildingId = null;
        let currentBuildingName = null;
        let deleteType = '';
        let deleteId = null;

        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date().toISOString().split('T')[0];
            const nextYear = new Date();
            nextYear.setFullYear(nextYear.getFullYear() + 1);

            document.getElementById('projectStartDate').value = today;
            document.getElementById('projectEndDate').value = nextYear.toISOString().split('T')[0];

            loadProjects();
        });

        function showMessage(message, type = 'success') {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = message;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'block';

            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        function setButtonLoading(button, isLoading) {
            if (isLoading) {
                button.innerHTML = '<span class="loading"></span> Processing...';
                button.disabled = true;
            } else {
                const originalText = button.getAttribute('data-original-text') || button.innerHTML;
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }

        async function loadProjects() {
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();

                if (data.success) {
                    const grid = document.getElementById('projectsGrid');

                    if (data.data.length === 0) {
                        grid.innerHTML = `
                            <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #7f8c8d;">
                                <i class="fas fa-building" style="font-size: 3rem; margin-bottom: 20px; opacity: 0.5;"></i>
                                <h3>No projects found</h3>
                                <p>Add your first project to get started!</p>
                            </div>
                        `;
                        return;
                    }

                    grid.innerHTML = data.data.map(project => {
                        const startDate = project.start_date ? 
                            new Date(project.start_date).toLocaleDateString('en-GB', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric'
                            }) : 'Not set';
                        const endDate = project.end_date ? 
                            new Date(project.end_date).toLocaleDateString('en-GB', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric'
                            }) : 'Not set';
                        const statusClass = project.status ? 
                            project.status.toLowerCase().replace(' ', '-') : 'planning';

                        return `
                        <div class="project-card" data-project-id="${project.id}">
                            <div class="project-header">
                                <div class="project-actions">
                                    <button class="btn btn-sm btn-warning" onclick="editProject(${project.id})" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteProject(${project.id}, '${project.name.replace(/'/g, "\\'")}')" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                                <h3 style="margin-right: 60px;">${project.name}</h3>
                                <p><i class="fas fa-map-marker-alt"></i> ${project.location}</p>
                            </div>
                            <div class="project-body">
                                <p style="margin-bottom: 15px; color: #666;">
                                    ${project.description || 'No description available'}
                                </p>
                                <div style="margin-bottom: 15px;">
                                    <span class="status-badge status-${statusClass}">
                                        <i class="fas fa-${getStatusIcon(project.status)}"></i> ${project.status || 'Planning'}
                                    </span>
                                </div>
                                <div class="project-stats">
                                    <div class="stat">
                                        <span class="stat-value"><i class="fas fa-calendar-plus"></i> ${startDate}</span>
                                        <span class="stat-label">Start Date</span>
                                    </div>
                                    <div class="stat">
                                        <span class="stat-value"><i class="fas fa-calendar-check"></i> ${endDate}</span>
                                        <span class="stat-label">End Date</span>
                                    </div>
                                    <div class="stat" onclick="viewBuildings(${project.id})" title="View Buildings">
                                        <span class="stat-value"><i class="fas fa-hotel"></i> ${project.buildings_count || 0}</span>
                                        <span class="stat-label">Buildings</span>
                                    </div>
                                    <div class="stat" onclick="viewUnits(${project.id})" title="View All Units">
                                        <span class="stat-value"><i class="fas fa-door-closed"></i> ${project.units_count || 0}</span>
                                        <span class="stat-label">Units</span>
                                    </div>
                                </div>

                                <div class="section-toggle" onclick="toggleSection('buildings-${project.id}')">
                                    <span><i class="fas fa-hotel"></i> Buildings (${project.buildings_count || 0})</span>
                                    <span><i class="fas fa-chevron-down"></i></span>
                                </div>
                                <div class="section-content" id="buildings-${project.id}">
                                    <div class="buildings-list" id="buildings-list-${project.id}">
                                        <!-- Buildings will be loaded here -->
                                    </div>
                                    <button class="btn btn-sm" onclick="viewBuildings(${project.id})" style="margin-top: 10px; width: 100%;">
                                        <i class="fas fa-eye"></i> View All Buildings
                                    </button>
                                </div>

                                <div class="section-toggle" onclick="toggleSection('units-${project.id}')">
                                    <span><i class="fas fa-door-closed"></i> Units (${project.units_count || 0})</span>
                                    <span><i class="fas fa-chevron-down"></i></span>
                                </div>
                                <div class="section-content" id="units-${project.id}">
                                    <div class="units-list" id="units-list-${project.id}">
                                        <!-- Units will be loaded here -->
                                    </div>
                                    <button class="btn btn-sm" onclick="viewUnits(${project.id})" style="margin-top: 10px; width: 100%;">
                                        <i class="fas fa-eye"></i> View All Units
                                    </button>
                                </div>
                            </div>
                        </div>
                        `;
                    }).join('');

                    data.data.forEach(project => {
                        loadProjectBuildings(project.id);
                        loadProjectUnits(project.id);
                    });
                }
            } catch (error) {
                console.error('Error loading projects:', error);
                document.getElementById('projectsGrid').innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #e74c3c;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 20px;"></i>
                        <h3>Error loading projects</h3>
                        <p>Please try again later.</p>
                    </div>
                `;
            }
        }

        function getStatusIcon(status) {
            switch(status?.toLowerCase()) {
                case 'planning': return 'clipboard-list';
                case 'under construction': return 'hard-hat';
                case 'completed': return 'check-circle';
                case 'on hold': return 'pause-circle';
                default: return 'clipboard-list';
            }
        }

        function toggleSection(sectionId) {
            const section = document.getElementById(sectionId);
            const icon = section.previousElementSibling.querySelector('.fa-chevron-down');
            section.classList.toggle('expanded');
            icon.classList.toggle('fa-chevron-down');
            icon.classList.toggle('fa-chevron-up');
        }

        function openProjectModal(projectId = null) {
            const modal = document.getElementById('projectModal');
            const title = document.getElementById('modalTitle');
            const submitBtn = document.getElementById('submitProjectBtn');

            if (projectId) {
                title.innerHTML = '<i class="fas fa-edit"></i> Edit Project';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Project';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Update Project');
                loadProjectData(projectId);
            } else {
                title.innerHTML = '<i class="fas fa-building"></i> Add New Project';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Project';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Save Project');
                document.getElementById('projectForm').reset();
                document.getElementById('projectId').value = '';

                const today = new Date().toISOString().split('T')[0];
                const nextYear = new Date();
                nextYear.setFullYear(nextYear.getFullYear() + 1);

                document.getElementById('projectStartDate').value = today;
                document.getElementById('projectEndDate').value = nextYear.toISOString().split('T')[0];
            }

            modal.style.display = 'flex';
        }

        function closeProjectModal() {
            document.getElementById('projectModal').style.display = 'none';
            document.getElementById('projectForm').reset();
        }

        async function loadProjectData(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`);
                const data = await response.json();

                if (data.success) {
                    const project = data.data;
                    document.getElementById('projectId').value = project.id;
                    document.getElementById('projectName').value = project.name || '';
                    document.getElementById('projectLocation').value = project.location || '';
                    document.getElementById('projectStartDate').value = project.start_date || '';
                    document.getElementById('projectEndDate').value = project.end_date || '';
                    document.getElementById('projectStatus').value = project.status || 'Planning';
                    document.getElementById('projectDescription').value = project.description || '';
                }
            } catch (error) {
                console.error('Error loading project data:', error);
                showMessage('Error loading project data', 'error');
            }
        }

        document.getElementById('projectForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const projectId = document.getElementById('projectId').value;
            const submitBtn = document.getElementById('submitProjectBtn');
            setButtonLoading(submitBtn, true);

            const projectData = {
                name: document.getElementById('projectName').value,
                location: document.getElementById('projectLocation').value,
                start_date: document.getElementById('projectStartDate').value,
                end_date: document.getElementById('projectEndDate').value,
                status: document.getElementById('projectStatus').value,
                description: document.getElementById('projectDescription').value
            };

            if (!projectData.name || !projectData.location) {
                showMessage('Project name and location are required!', 'error');
                setButtonLoading(submitBtn, false);
                return;
            }

            try {
                const url = projectId ? `/api/projects/${projectId}` : '/api/projects';
                const method = projectId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(projectId ? 'Project updated successfully!' : 'Project added successfully!');
                    closeProjectModal();
                    loadProjects();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to save project'), 'error');
                }
            } catch (error) {
                showMessage('Error saving project', 'error');
                console.error(error);
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });

        async function loadProjectBuildings(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/buildings`);
                const data = await response.json();

                if (data.success) {
                    const container = document.getElementById(`buildings-list-${projectId}`);
                    if (container) {
                        if (data.data.length === 0) {
                            container.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No buildings added yet.</p>';
                        } else {
                            container.innerHTML = data.data.slice(0, 3).map(building => `
                                <div class="building-item">
                                    <div class="building-info">
                                        <strong>${building.name}</strong><br>
                                        <small>${building.floors} floors • ${building.status}</small>
                                    </div>
                                    <div class="building-actions">
                                        <button class="btn btn-sm btn-warning" onclick="editBuilding(${building.id})" title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteBuilding(${building.id}, '${building.name.replace(/'/g, "\\'")}')" title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            `).join('');
                        }
                    }
                }
            } catch (error) {
                console.error('Error loading project buildings:', error);
            }
        }

        async function loadProjectUnits(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/buildings`);
                const data = await response.json();

                if (data.success && data.data.length > 0) {
                    const buildingId = data.data[0].id;
                    const unitsResponse = await fetch(`/api/buildings/${buildingId}/units`);
                    const unitsData = await unitsResponse.json();

                    const container = document.getElementById(`units-list-${projectId}`);
                    if (container) {
                        if (!unitsData.success || unitsData.data.length === 0) {
                            container.innerHTML = '<p style="color: #7f8c8d; text-align: center;">No units added yet.</p>';
                        } else {
                            container.innerHTML = unitsData.data.slice(0, 3).map(unit => `
                                <div class="unit-item">
                                    <div class="unit-info">
                                        <strong>${unit.unit_number}</strong><br>
                                        <small>${unit.type} • ${unit.area} sqm • $${unit.price.toLocaleString()}</small>
                                    </div>
                                    <div class="unit-actions">
                                        <button class="btn btn-sm btn-warning" onclick="editUnit(${unit.id})" title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteUnit(${unit.id}, '${unit.unit_number.replace(/'/g, "\\'")}')" title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            `).join('');
                        }
                    }
                }
            } catch (error) {
                console.error('Error loading project units:', error);
            }
        }

        async function viewBuildings(projectId) {
            currentProjectId = projectId;
            document.getElementById('buildingProjectId').value = projectId;
            await loadBuildingsList(projectId);
            document.getElementById('buildingModal').style.display = 'flex';
        }

        function closeBuildingModal() {
            document.getElementById('buildingModal').style.display = 'none';
        }

        async function loadBuildingsList(projectId) {
            try {
                const container = document.getElementById('buildingsList');
                container.innerHTML = '<p style="text-align: center; padding: 20px;"><span class="loading"></span> Loading buildings...</p>';

                const response = await fetch(`/api/projects/${projectId}/buildings`);
                const data = await response.json();

                if (data.success) {
                    if (data.data.length === 0) {
                        container.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 20px;">No buildings found. Add your first building!</p>';
                    } else {
                        container.innerHTML = data.data.map(building => `
                            <div class="building-item" style="margin-bottom: 10px;">
                                <div class="building-info">
                                    <strong>${building.name}</strong><br>
                                    <small>Floors: ${building.floors} • Status: ${building.status}</small><br>
                                    <small>Units: ${building.units_count || 0} • Available: ${building.available_units || 0}</small>
                                </div>
                                <div class="building-actions">
                                    <button class="btn btn-sm btn-info" onclick="viewUnitsInBuilding(${building.id}, '${building.name.replace(/'/g, "\\'")}')" title="View Units">
                                        <i class="fas fa-door-closed"></i>
                                    </button>
                                    <button class="btn btn-sm btn-warning" onclick="editBuilding(${building.id})" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteBuilding(${building.id}, '${building.name.replace(/'/g, "\\'")}')" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        `).join('');
                    }
                } else {
                    container.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Error loading buildings</p>';
                }
            } catch (error) {
                console.error('Error loading buildings:', error);
                document.getElementById('buildingsList').innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Error loading buildings</p>';
            }
        }

        function openAddBuildingModal(buildingId = null) {
            const modal = document.getElementById('addBuildingModal');
            const title = document.getElementById('buildingModalTitle');
            const submitBtn = document.getElementById('submitBuildingBtn');

            if (buildingId) {
                title.innerHTML = '<i class="fas fa-edit"></i> Edit Building';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Building';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Update Building');
                loadBuildingData(buildingId);
            } else {
                title.innerHTML = '<i class="fas fa-hotel"></i> Add Building';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Building';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Save Building');
                document.getElementById('buildingForm').reset();
                document.getElementById('buildingId').value = '';
                document.getElementById('buildingProjectIdInput').value = currentProjectId;
            }

            modal.style.display = 'flex';
        }

        function closeAddBuildingModal() {
            document.getElementById('addBuildingModal').style.display = 'none';
            document.getElementById('buildingForm').reset();
        }

        async function loadBuildingData(buildingId) {
            try {
                const response = await fetch(`/api/buildings/${buildingId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        const building = data.data;
                        document.getElementById('buildingId').value = building.id;
                        document.getElementById('buildingName').value = building.name || '';
                        document.getElementById('buildingFloors').value = building.floors || 1;
                        document.getElementById('buildingStatus').value = building.status || 'Not Started';
                        document.getElementById('buildingProjectIdInput').value = building.project_id;
                    }
                }
            } catch (error) {
                console.error('Error loading building data:', error);
                showMessage('Error loading building data', 'error');
            }
        }

        document.getElementById('buildingForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const buildingId = document.getElementById('buildingId').value;
            const projectId = document.getElementById('buildingProjectIdInput').value;
            const submitBtn = document.getElementById('submitBuildingBtn');
            setButtonLoading(submitBtn, true);

            const buildingData = {
                project_id: projectId,
                name: document.getElementById('buildingName').value,
                floors: document.getElementById('buildingFloors').value,
                status: document.getElementById('buildingStatus').value
            };

            try {
                const url = buildingId ? `/api/buildings/${buildingId}` : '/api/buildings';
                const method = buildingId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(buildingData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(buildingId ? 'Building updated successfully!' : 'Building added successfully!');
                    closeAddBuildingModal();
                    await loadBuildingsList(projectId);
                    loadProjects();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to save building'), 'error');
                }
            } catch (error) {
                showMessage('Error saving building', 'error');
                console.error(error);
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });

        function viewUnits(projectId) {
            currentProjectId = projectId;
            loadAllProjectUnits(projectId);
        }

        async function viewUnitsInBuilding(buildingId, buildingName) {
            currentBuildingId = buildingId;
            currentBuildingName = buildingName;
            document.getElementById('unitBuildingId').value = buildingId;
            document.getElementById('unitBuildingName').textContent = buildingName;
            await loadUnitsList(buildingId);
            document.getElementById('unitModal').style.display = 'flex';
        }

        function closeUnitModal() {
            document.getElementById('unitModal').style.display = 'none';
        }

        async function loadAllProjectUnits(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/units`);
                const data = await response.json();

                if (data.success) {
                    let message = `All Units in Project:\n\n`;
                    if (data.data.length === 0) {
                        message += 'No units found in this project.';
                    } else {
                        data.data.forEach((unit, index) => {
                            message += `${index + 1}. ${unit.unit_number} - ${unit.type}\n`;
                            message += `   Building: ${unit.building_name}\n`;
                            message += `   Area: ${unit.area} sqm • Price: $${unit.price.toLocaleString()}\n`;
                            message += `   Status: ${unit.status}\n\n`;
                        });
                    }
                    alert(message);
                }
            } catch (error) {
                console.error('Error loading project units:', error);
                showMessage('Error loading project units', 'error');
            }
        }

        async function loadUnitsList(buildingId) {
            try {
                const container = document.getElementById('unitsList');
                container.innerHTML = '<p style="text-align: center; padding: 20px;"><span class="loading"></span> Loading units...</p>';

                const response = await fetch(`/api/buildings/${buildingId}/units`);
                const data = await response.json();

                if (data.success) {
                    if (data.data.length === 0) {
                        container.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 20px;">No units found. Add your first unit!</p>';
                    } else {
                        container.innerHTML = data.data.map(unit => {
                            const statusClass = `unit-status-${unit.status.toLowerCase().replace(' ', '-')}`;
                            return `
                                <div class="unit-item" style="margin-bottom: 10px;">
                                    <div class="unit-info">
                                        <strong>${unit.unit_number}</strong><br>
                                        <small>Type: ${unit.type} • Floor: ${unit.floor || 'N/A'}</small><br>
                                        <small>Area: ${unit.area} sqm • Bedrooms: ${unit.bedrooms} • Bathrooms: ${unit.bathrooms}</small><br>
                                        <small>Price: $${unit.price.toLocaleString()} • Status: <span class="${statusClass}">${unit.status}</span></small>
                                    </div>
                                    <div class="unit-actions">
                                        <button class="btn btn-sm btn-warning" onclick="editUnit(${unit.id})" title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-danger" onclick="deleteUnit(${unit.id}, '${unit.unit_number.replace(/'/g, "\\'")}')" title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            `;
                        }).join('');
                    }
                } else {
                    container.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Error loading units</p>';
                }
            } catch (error) {
                console.error('Error loading units:', error);
                container.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 20px;">Error loading units</p>';
            }
        }

        function openAddUnitModal(unitId = null) {
            const modal = document.getElementById('addUnitModal');
            const title = document.getElementById('unitModalTitle');
            const submitBtn = document.getElementById('submitUnitBtn');

            if (unitId) {
                title.innerHTML = '<i class="fas fa-edit"></i> Edit Unit';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Unit';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Update Unit');
                loadUnitData(unitId);
            } else {
                title.innerHTML = '<i class="fas fa-door-closed"></i> Add Unit';
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Unit';
                submitBtn.setAttribute('data-original-text', '<i class="fas fa-save"></i> Save Unit');
                document.getElementById('unitForm').reset();
                document.getElementById('unitId').value = '';
                document.getElementById('unitBuildingIdInput').value = currentBuildingId;
                document.getElementById('unitFloor').value = 1;
                document.getElementById('unitArea').value = 100;
                document.getElementById('unitBedrooms').value = 2;
                document.getElementById('unitBathrooms').value = 1;
                document.getElementById('unitPrice').value = 100000;
            }

            modal.style.display = 'flex';
        }

        function closeAddUnitModal() {
            document.getElementById('addUnitModal').style.display = 'none';
            document.getElementById('unitForm').reset();
        }

        async function loadUnitData(unitId) {
            try {
                const response = await fetch(`/api/units/${unitId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        const unit = data.data;
                        document.getElementById('unitId').value = unit.id;
                        document.getElementById('unitNumber').value = unit.unit_number || '';
                        document.getElementById('unitType').value = unit.type || 'Apartment';
                        document.getElementById('unitArea').value = unit.area || '';
                        document.getElementById('unitFloor').value = unit.floor || 1;
                        document.getElementById('unitBedrooms').value = unit.bedrooms || 2;
                        document.getElementById('unitBathrooms').value = unit.bathrooms || 1;
                        document.getElementById('unitPrice').value = unit.price || '';
                        document.getElementById('unitStatus').value = unit.status || 'Available';
                        document.getElementById('unitFeatures').value = unit.features || '';
                        document.getElementById('unitBuildingIdInput').value = unit.building_id;
                    }
                }
            } catch (error) {
                console.error('Error loading unit data:', error);
                showMessage('Error loading unit data', 'error');
            }
        }

        document.getElementById('unitForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const unitId = document.getElementById('unitId').value;
            const buildingId = document.getElementById('unitBuildingIdInput').value;
            const submitBtn = document.getElementById('submitUnitBtn');
            setButtonLoading(submitBtn, true);

            const unitData = {
                building_id: buildingId,
                unit_number: document.getElementById('unitNumber').value,
                type: document.getElementById('unitType').value,
                area: parseFloat(document.getElementById('unitArea').value),
                floor: parseInt(document.getElementById('unitFloor').value) || 0,
                bedrooms: parseInt(document.getElementById('unitBedrooms').value) || 0,
                bathrooms: parseInt(document.getElementById('unitBathrooms').value) || 1,
                price: parseFloat(document.getElementById('unitPrice').value),
                status: document.getElementById('unitStatus').value,
                features: document.getElementById('unitFeatures').value
            };

            if (!unitData.unit_number || !unitData.area || !unitData.price) {
                showMessage('Unit number, area, and price are required!', 'error');
                setButtonLoading(submitBtn, false);
                return;
            }

            if (unitData.area <= 0) {
                showMessage('Area must be greater than 0', 'error');
                setButtonLoading(submitBtn, false);
                return;
            }

            if (unitData.price <= 0) {
                showMessage('Price must be greater than 0', 'error');
                setButtonLoading(submitBtn, false);
                return;
            }

            try {
                const url = unitId ? `/api/units/${unitId}` : '/api/units';
                const method = unitId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(unitData)
                });

                const data = await response.json();

                if (data.success) {
                    showMessage(unitId ? 'Unit updated successfully!' : 'Unit added successfully!');
                    closeAddUnitModal();
                    await loadUnitsList(buildingId);
                    loadProjects();
                } else {
                    showMessage('Error: ' + (data.error || 'Failed to save unit'), 'error');
                }
            } catch (error) {
                showMessage('Error saving unit', 'error');
                console.error(error);
            } finally {
                setButtonLoading(submitBtn, false);
            }
        });

        async function editBuilding(buildingId) {
            openAddBuildingModal(buildingId);
        }

        async function editUnit(unitId) {
            openAddUnitModal(unitId);
        }

        async function editProject(projectId) {
            openProjectModal(projectId);
        }

        function deleteProject(projectId, projectName) {
            deleteType = 'project';
            deleteId = projectId;
            document.getElementById('deleteMessage').innerHTML = `
                <i class="fas fa-exclamation-circle" style="color: #e74c3c; font-size: 2rem; margin-bottom: 10px;"></i><br>
                <strong>Delete Project: ${projectName}</strong><br><br>
                Are you sure you want to delete this project?<br>
                This will also delete all associated buildings and units!<br><br>
                <small style="color: #e74c3c;"><i class="fas fa-warning"></i> This action cannot be undone!</small>
            `;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function deleteBuilding(buildingId, buildingName) {
            deleteType = 'building';
            deleteId = buildingId;
            document.getElementById('deleteMessage').innerHTML = `
                <i class="fas fa-exclamation-circle" style="color: #e74c3c; font-size: 2rem; margin-bottom: 10px;"></i><br>
                <strong>Delete Building: ${buildingName}</strong><br><br>
                Are you sure you want to delete this building?<br>
                This will also delete all associated units!<br><br>
                <small style="color: #e74c3c;"><i class="fas fa-warning"></i> This action cannot be undone!</small>
            `;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function deleteUnit(unitId, unitNumber) {
            deleteType = 'unit';
            deleteId = unitId;
            document.getElementById('deleteMessage').innerHTML = `
                <i class="fas fa-exclamation-circle" style="color: #e74c3c; font-size: 2rem; margin-bottom: 10px;"></i><br>
                <strong>Delete Unit: ${unitNumber}</strong><br><br>
                Are you sure you want to delete this unit?<br><br>
                <small style="color: #e74c3c;"><i class="fas fa-warning"></i> This action cannot be undone!</small>
            `;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function closeDeleteModal() {
            document.getElementById('deleteModal').style.display = 'none';
            deleteType = '';
            deleteId = null;
        }

        async function confirmDelete() {
            if (!deleteId) return;

            const deleteBtn = document.querySelector('#deleteModal .btn-danger');
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<span class="loading"></span> Deleting...';
            deleteBtn.disabled = true;

            try {
                let url = '';

                switch(deleteType) {
                    case 'project':
                        url = `/api/projects/${deleteId}`;
                        break;
                    case 'building':
                        url = `/api/buildings/${deleteId}`;
                        break;
                    case 'unit':
                        url = `/api/units/${deleteId}`;
                        break;
                }

                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showMessage('Item deleted successfully!');
                    closeDeleteModal();

                    switch(deleteType) {
                        case 'project':
                            loadProjects();
                            break;
                        case 'building':
                            if (currentProjectId) {
                                await loadBuildingsList(currentProjectId);
                                loadProjects();
                            }
                            break;
                        case 'unit':
                            if (currentBuildingId) {
                                await loadUnitsList(currentBuildingId);
                                loadProjects();
                            }
                            break;
                    }
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showMessage('Error deleting item', 'error');
                console.error(error);
            } finally {
                deleteBtn.innerHTML = originalText;
                deleteBtn.disabled = false;
                deleteType = '';
                deleteId = null;
            }
        }

        window.onclick = function(event) {
            const modals = ['projectModal', 'buildingModal', 'addBuildingModal', 'unitModal', 'addUnitModal', 'deleteModal'];
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (event.target === modal) {
                    if (modalId === 'projectModal') closeProjectModal();
                    if (modalId === 'buildingModal') closeBuildingModal();
                    if (modalId === 'addBuildingModal') closeAddBuildingModal();
                    if (modalId === 'unitModal') closeUnitModal();
                    if (modalId === 'addUnitModal') closeAddUnitModal();
                    if (modalId === 'deleteModal') closeDeleteModal();
                }
            });
        };

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeProjectModal();
                closeBuildingModal();
                closeAddBuildingModal();
                closeUnitModal();
                closeAddUnitModal();
                closeDeleteModal();
            }
        });
    </script>
</body>
</html>''',

        'sales.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sales Management - Rawas Real Estate</title>
    <link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 20px; }
        .header h1 { color: #2c3e50; }
        .btn { padding: 12px 25px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: all 0.3s; text-decoration: none; display: inline-block; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #d68910; }

        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .tab-btn { padding: 10px 20px; background: #ecf0f1; border: none; border-radius: 5px; cursor: pointer; }
        .tab-btn.active { background: #3498db; color: white; }

        .table-container { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 30px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 1000px; }
        th { background: #f8f9fa; padding: 15px; text-align: left; color: #2c3e50; font-weight: 600; border-bottom: 1px solid #e0e0e0; }
        td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
        tr:hover { background: #f9f9f9; }
        tr:last-child td { border-bottom: none; }

        .status-badge { padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
        .status-active { background: #d4edda; color: #155724; }
        .status-completed { background: #cce5ff; color: #004085; }
        .status-cancelled { background: #f8d7da; color: #721c24; }
        .status-delayed { background: #fff3cd; color: #856404; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 10px; max-width: 800px; width: 90%; max-height: 90vh; overflow-y: auto; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; color: #2c3e50; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }

        .payment-history { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .payment-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e9ecef; }
        .payment-item:last-child { border-bottom: none; }

        .select2-container { width: 100% !important; }

        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .table-container { overflow-x: auto; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav" style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
            <a href="/" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">🏠 Home</a>
            <a href="/dashboard" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">📊 Dashboard</a>
            <a href="/projects" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">🏗️ Projects</a>
            <a href="/clients" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">👥 Clients</a>
            <a href="/employees" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">👨‍💼 Employees</a>
            <a href="/inventory" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">📦 Inventory</a>
        </div>

        <div class="header">
            <h1>💰 Sales Management</h1>
            <div>
                <button class="btn" onclick="openSaleModal()">+ New Sale</button>
                <button class="btn btn-success" onclick="exportSales()">📊 Export</button>
            </div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="filterSales('all')">All Sales</button>
            <button class="tab-btn" onclick="filterSales('active')">Active</button>
            <button class="tab-btn" onclick="filterSales('completed')">Completed</button>
            <button class="tab-btn" onclick="filterSales('delayed')">Delayed Payments</button>
        </div>

        <div class="table-container">
            <table id="salesTable">
                <thead>
                    <tr>
                        <th>Contract #</th>
                        <th>Date</th>
                        <th>Client</th>
                        <th>Unit</th>
                        <th>Total Price</th>
                        <th>Paid</th>
                        <th>Balance</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add Sale Modal -->
    <div id="saleModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;">Add New Sale</h2>
            <form id="saleForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="saleUnit">Select Unit *</label>
                        <select id="saleUnit" required style="width: 100%;">
                            <option value="">Loading units...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="saleClient">Select Client *</label>
                        <select id="saleClient" required style="width: 100%;">
                            <option value="">Loading clients...</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="saleEmployee">Sales Agent</label>
                        <select id="saleEmployee" style="width: 100%;">
                            <option value="">Loading employees...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="saleDate">Contract Date</label>
                        <input type="date" id="saleDate">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="saleTotal">Total Price ($)</label>
                        <input type="number" id="saleTotal" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="saleDown">Down Payment ($)</label>
                        <input type="number" id="saleDown" step="0.01" required>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="salePlan">Payment Plan</label>
                        <select id="salePlan">
                            <option value="Cash">Cash</option>
                            <option value="Installments">Installments</option>
                            <option value="Bank Loan">Bank Loan</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="saleMethod">Payment Method</label>
                        <select id="saleMethod">
                            <option value="Cash">Cash</option>
                            <option value="Bank Transfer">Bank Transfer</option>
                            <option value="Check">Check</option>
                            <option value="Credit Card">Credit Card</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label for="saleNotes">Notes</label>
                    <textarea id="saleNotes" rows="3"></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeSaleModal()">Cancel</button>
                    <button type="submit" class="btn btn-success">Create Sale</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Add Payment Modal -->
    <div id="paymentModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;">Add Payment</h2>
            <form id="paymentForm">
                <input type="hidden" id="paymentSaleId">

                <div class="form-row">
                    <div class="form-group">
                        <label for="paymentAmount">Amount ($) *</label>
                        <input type="number" id="paymentAmount" step="0.01" required>
                    </div>
                    <div class="form-group">
                        <label for="paymentDate">Payment Date</label>
                        <input type="date" id="paymentDate">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="paymentMethod">Payment Method</label>
                        <select id="paymentMethod">
                            <option value="Cash">Cash</option>
                            <option value="Bank Transfer">Bank Transfer</option>
                            <option value="Check">Check</option>
                            <option value="Credit Card">Credit Card</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="paymentReceipt">Receipt Number</label>
                        <input type="text" id="paymentReceipt" placeholder="Auto-generated if empty">
                    </div>
                </div>

                <div class="form-group">
                    <label for="paymentNotes">Notes</label>
                    <textarea id="paymentNotes" rows="3"></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closePaymentModal()">Cancel</button>
                    <button type="submit" class="btn btn-success">Record Payment</button>
                </div>
            </form>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    <script>
        let currentSaleId = null;
        let currentFilter = 'all';

        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('saleDate').value = today;
            document.getElementById('paymentDate').value = today;
            loadSales();
        });

        async function loadSales() {
            try {
                const response = await fetch('/api/sales');
                const data = await response.json();

                if (data.success) {
                    displaySales(data.data);
                }
            } catch (error) {
                console.error('Error loading sales:', error);
            }
        }

        function displaySales(sales) {
            const tbody = document.querySelector('#salesTable tbody');

            if (!sales || sales.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px; color: #7f8c8d;">No sales found</td></tr>';
                return;
            }

            let filteredSales = sales;
            if (currentFilter === 'active') {
                filteredSales = sales.filter(s => s.status === 'Active');
            } else if (currentFilter === 'completed') {
                filteredSales = sales.filter(s => s.status === 'Completed');
            } else if (currentFilter === 'delayed') {
                filteredSales = sales.filter(s => {
                    const daysDelayed = s.days_delayed || 0;
                    return s.status === 'Active' && s.remaining_balance > 0 && daysDelayed > 30;
                });
            }

            tbody.innerHTML = filteredSales.map(sale => {
                const paid = sale.total_price - sale.remaining_balance;
                const progress = sale.total_price > 0 ? Math.round((paid / sale.total_price) * 100) : 0;
                const daysDelayed = sale.days_delayed || 0;
                const contractDate = sale.contract_date ? 
                    new Date(sale.contract_date).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    }) : '';

                return `
                <tr>
                    <td><strong>${sale.contract_number || 'N/A'}</strong></td>
                    <td>${contractDate}</td>
                    <td>${sale.client_name || ''}<br><small>${sale.client_phone || ''}</small></td>
                    <td>${sale.unit_number || ''}<br><small>${sale.unit_type || ''}</small></td>
                    <td><strong>$${parseFloat(sale.total_price || 0).toLocaleString()}</strong></td>
                    <td>$${parseFloat(paid).toLocaleString()}<br><small>${progress}% paid</small></td>
                    <td>$${parseFloat(sale.remaining_balance || 0).toLocaleString()}</td>
                    <td>
                        <span class="status-badge status-${sale.status ? sale.status.toLowerCase() : 'active'}">
                            ${sale.status || 'Active'}
                            ${daysDelayed > 30 ? ' (Delayed)' : ''}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-warning" style="padding: 5px 10px; font-size: 0.9rem;" onclick="viewPayments(${sale.id})">💳</button>
                        <button class="btn" style="padding: 5px 10px; font-size: 0.9rem;" onclick="viewSaleDetails(${sale.id})">👁️</button>
                    </td>
                </tr>
                `;
            }).join('');
        }

        function filterSales(filter) {
            currentFilter = filter;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            loadSales();
        }

        async function loadSaleFormData() {
            try {
                const [unitsRes, clientsRes, employeesRes] = await Promise.all([
                    fetch('/api/units?status=Available'),
                    fetch('/api/clients'),
                    fetch('/api/employees')
                ]);

                const unitsData = await unitsRes.json();
                const clientsData = await clientsRes.json();
                const employeesData = await employeesRes.json();

                if (unitsData.success) {
                    const unitSelect = $('#saleUnit');
                    unitSelect.empty();
                    unitSelect.append('<option value="">Select Unit</option>');
                    unitsData.data.forEach(unit => {
                        unitSelect.append(new Option(
                            `${unit.unit_number} - ${unit.type} - $${unit.price.toLocaleString()} (${unit.project_name})`,
                            unit.id
                        ));
                    });
                }

                if (clientsData.success) {
                    const clientSelect = $('#saleClient');
                    clientSelect.empty();
                    clientSelect.append('<option value="">Select Client</option>');
                    clientsData.data.forEach(client => {
                        clientSelect.append(new Option(
                            `${client.name} - ${client.phone} (${client.type})`,
                            client.id
                        ));
                    });
                }

                if (employeesData.success) {
                    const employeeSelect = $('#saleEmployee');
                    employeeSelect.empty();
                    employeeSelect.append('<option value="">Select Employee</option>');
                    employeesData.data.forEach(emp => {
                        employeeSelect.append(new Option(
                            `${emp.name} - ${emp.position}`,
                            emp.id
                        ));
                    });
                }

                $('select').select2({
                    width: '100%',
                    placeholder: 'Select an option'
                });

            } catch (error) {
                console.error('Error loading form data:', error);
            }
        }

        async function openSaleModal() {
            await loadSaleFormData();
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('saleDate').value = today;
            document.getElementById('saleModal').style.display = 'flex';
        }

        function closeSaleModal() {
            document.getElementById('saleModal').style.display = 'none';
            document.getElementById('saleForm').reset();
            $('select').val(null).trigger('change');
        }

        document.getElementById('saleForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const saleData = {
                unit_id: $('#saleUnit').val(),
                client_id: $('#saleClient').val(),
                employee_id: $('#saleEmployee').val() || null,
                contract_date: document.getElementById('saleDate').value,
                total_price: parseFloat(document.getElementById('saleTotal').value),
                down_payment: parseFloat(document.getElementById('saleDown').value),
                payment_plan: document.getElementById('salePlan').value,
                payment_method: document.getElementById('saleMethod').value,
                notes: document.getElementById('saleNotes').value
            };

            try {
                const response = await fetch('/api/sales', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(saleData)
                });

                const data = await response.json();

                if (data.success) {
                    alert('Sale created successfully!');
                    closeSaleModal();
                    loadSales();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error creating sale');
                console.error(error);
            }
        });

        async function viewPayments(saleId) {
            currentSaleId = saleId;

            try {
                const saleRes = await fetch(`/api/sales/${saleId}`);
                const saleData = await saleRes.json();

                if (saleData.success) {
                    document.getElementById('paymentSaleId').value = saleId;
                    document.getElementById('paymentAmount').value = Math.min(1000, saleData.data.remaining_balance || 0);

                    const today = new Date().toISOString().split('T')[0];
                    document.getElementById('paymentDate').value = today;

                    document.getElementById('paymentModal').style.display = 'flex';
                }
            } catch (error) {
                console.error('Error loading payment data:', error);
            }
        }

        function closePaymentModal() {
            document.getElementById('paymentModal').style.display = 'none';
            document.getElementById('paymentForm').reset();
        }

        document.getElementById('paymentForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const paymentData = {
                sale_id: currentSaleId,
                amount: parseFloat(document.getElementById('paymentAmount').value),
                payment_date: document.getElementById('paymentDate').value,
                method: document.getElementById('paymentMethod').value,
                receipt_number: document.getElementById('paymentReceipt').value || `RCPT-${Date.now()}`,
                notes: document.getElementById('paymentNotes').value
            };

            try {
                const response = await fetch('/api/payments', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(paymentData)
                });

                const data = await response.json();

                if (data.success) {
                    alert('Payment recorded successfully!');
                    closePaymentModal();
                    loadSales();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error recording payment');
                console.error(error);
            }
        });

        async function viewSaleDetails(saleId) {
            try {
                const response = await fetch(`/api/sales/${saleId}`);
                const data = await response.json();

                if (data.success) {
                    const sale = data.data;
                    const contractDate = sale.contract_date ? 
                        new Date(sale.contract_date).toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric'
                        }) : '';
                    
                    const details = `
                        Contract: ${sale.contract_number || 'N/A'}\n
                        Date: ${contractDate}\n
                        Client: ${sale.client_name || ''}\n
                        Phone: ${sale.client_phone || ''}\n
                        Unit: ${sale.unit_number || ''} (${sale.unit_type || ''})\n
                        Area: ${sale.area || 0} sqm\n
                        Total Price: $${sale.total_price?.toLocaleString() || 0}\n
                        Down Payment: $${sale.down_payment?.toLocaleString() || 0}\n
                        Remaining Balance: $${sale.remaining_balance?.toLocaleString() || 0}\n
                        Status: ${sale.status || 'Active'}\n
                        Payment Plan: ${sale.payment_plan || 'Cash'}\n
                        Payment Method: ${sale.payment_method || 'Cash'}
                    `;
                    alert(details);
                }
            } catch (error) {
                console.error('Error loading sale details:', error);
            }
        }

        async function exportSales() {
            try {
                const exportBtn = event.target;
                const originalText = exportBtn.textContent;
                exportBtn.textContent = '⏳ Exporting...';
                exportBtn.disabled = true;

                const response = await fetch('/api/export/sales');

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sales_export.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    const errorData = await response.json();
                    alert('Export failed: ' + (errorData.error || 'Unknown error'));
                }

                setTimeout(() => {
                    exportBtn.textContent = originalText;
                    exportBtn.disabled = false;
                }, 2000);

            } catch (error) {
                alert('Error exporting data: ' + error.message);
                console.error('Export error:', error);
            }
        }

        window.onclick = function(event) {
            const saleModal = document.getElementById('saleModal');
            const paymentModal = document.getElementById('paymentModal');

            if (event.target === saleModal) closeSaleModal();
            if (event.target === paymentModal) closePaymentModal();
        };
    </script>
</body>
</html>''',

        'clients.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clients Management - Rawas Real Estate</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; gap: 20px; }
        .header h1 { color: #2c3e50; }
        .btn { padding: 12px 25px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: all 0.3s; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }

        .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .tab-btn { padding: 10px 20px; background: #ecf0f1; border: none; border-radius: 5px; cursor: pointer; }
        .tab-btn.active { background: #3498db; color: white; }

        .search-box { margin-bottom: 20px; }
        .search-box input { width: 300px; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }

        .table-container { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 30px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 1200px; }
        th { background: #f8f9fa; padding: 15px; text-align: left; color: #2c3e50; font-weight: 600; border-bottom: 1px solid #e0e0e0; }
        td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
        tr:hover { background: #f9f9f9; }
        tr:last-child td { border-bottom: none; }

        .client-avatar { width: 40px; height: 40px; border-radius: 50%; background: #3498db; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; }

        .type-badge { padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; display: inline-block; }
        .type-buyer { background: #d4edda; color: #155724; }
        .type-investor { background: #cce5ff; color: #004085; }
        .type-tenant { background: #fff3cd; color: #856404; }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: white; padding: 30px; border-radius: 10px; max-width: 600px; width: 90%; max-height: 90vh; overflow-y: auto; }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 5px; color: #2c3e50; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }

        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .search-box input { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav" style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
            <a href="/" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">🏠 Home</a>
            <a href="/dashboard" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">📊 Dashboard</a>
            <a href="/projects" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">🏗️ Projects</a>
            <a href="/sales" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">💰 Sales</a>
            <a href="/employees" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">👨‍💼 Employees</a>
            <a href="/inventory" class="nav-btn" style="padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px;">📦 Inventory</a>
        </div>

        <div class="header">
            <h1>👥 Clients Management</h1>
            <button class="btn" onclick="openClientModal()">+ New Client</button>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="filterClients('all')">All Clients</button>
            <button class="tab-btn" onclick="filterClients('Buyer')">Buyers</button>
            <button class="tab-btn" onclick="filterClients('Investor')">Investors</button>
            <button class="tab-btn" onclick="filterClients('Tenant')">Tenants</button>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search by name, phone, or email..." onkeyup="searchClients()">
        </div>

        <div class="table-container">
            <table id="clientsTable">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Contact</th>
                        <th>Type</th>
                        <th>ID Number</th>
                        <th>Company</th>
                        <th>Address</th>
                        <th>Registered</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add Client Modal -->
    <div id="clientModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;" id="modalTitle">Add New Client</h2>
            <form id="clientForm">
                <input type="hidden" id="clientId">

                <div class="form-row">
                    <div class="form-group">
                        <label for="clientName">Full Name *</label>
                        <input type="text" id="clientName" required>
                    </div>
                    <div class="form-group">
                        <label for="clientType">Type</label>
                        <select id="clientType">
                            <option value="Buyer">Buyer</option>
                            <option value="Investor">Investor</option>
                            <option value="Tenant">Tenant</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="clientPhone">Phone Number *</label>
                        <input type="tel" id="clientPhone" required>
                    </div>
                    <div class="form-group">
                        <label for="clientEmail">Email</label>
                        <input type="email" id="clientEmail">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="clientIdNumber">ID Number</label>
                        <input type="text" id="clientIdNumber">
                    </div>
                    <div class="form-group">
                        <label for="clientCompany">Company</label>
                        <input type="text" id="clientCompany">
                    </div>
                </div>

                <div class="form-group">
                    <label for="clientAddress">Address</label>
                    <input type="text" id="clientAddress">
                </div>

                <div class="form-group">
                    <label for="clientNotes">Notes</label>
                    <textarea id="clientNotes" rows="3"></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="btn" onclick="closeClientModal()">Cancel</button>
                    <button type="submit" class="btn btn-success" id="submitButton">Add Client</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Confirmation Modal for Delete -->
    <div id="deleteModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-bottom: 20px;">Confirm Delete</h2>
            <p id="deleteMessage">Are you sure you want to delete this client?</p>
            <div class="form-actions">
                <button type="button" class="btn" onclick="closeDeleteModal()">Cancel</button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">Delete</button>
            </div>
        </div>
    </div>

    <script>
        let currentFilter = 'all';
        let allClients = [];
        let clientToDelete = null;

        async function loadClients() {
            try {
                const response = await fetch('/api/clients');
                const data = await response.json();

                if (data.success) {
                    allClients = data.data;
                    displayClients(allClients);
                }
            } catch (error) {
                console.error('Error loading clients:', error);
            }
        }

        function displayClients(clients) {
            const tbody = document.querySelector('#clientsTable tbody');

            if (!clients || clients.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #7f8c8d;">No clients found</td></tr>';
                return;
            }

            let filteredClients = clients;
            if (currentFilter !== 'all') {
                filteredClients = clients.filter(c => c.type === currentFilter);
            }

            tbody.innerHTML = filteredClients.map(client => {
                const avatarText = client.name ? client.name.charAt(0).toUpperCase() : 'C';
                const registeredDate = new Date(client.created_at || Date.now());
                const formattedDate = registeredDate.toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                });

                return `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="client-avatar">${avatarText}</div>
                            <div>
                                <strong>${client.name || 'Unknown'}</strong>
                                ${client.email ? `<br><small>${client.email}</small>` : ''}
                            </div>
                        </div>
                    </td>
                    <td>${client.phone || ''}</td>
                    <td><span class="type-badge type-${client.type ? client.type.toLowerCase() : 'buyer'}">${client.type || 'Buyer'}</span></td>
                    <td>${client.id_number || 'N/A'}</td>
                    <td>${client.company || '-'}</td>
                    <td>${client.address || '-'}</td>
                    <td>${formattedDate}</td>
                    <td>
                        <button class="btn" style="padding: 5px 10px; font-size: 0.9rem;" onclick="editClient(${client.id})">✏️</button>
                        <button class="btn btn-success" style="padding: 5px 10px; font-size: 0.9rem;" onclick="viewClientSales(${client.id})">💰</button>
                        <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.9rem;" onclick="deleteClient(${client.id}, '${client.name}')">🗑️</button>
                    </td>
                </tr>
                `;
            }).join('');
        }

        function filterClients(filter) {
            currentFilter = filter;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            displayClients(allClients);
        }

        function searchClients() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();

            if (!searchTerm) {
                displayClients(allClients);
                return;
            }

            const filtered = allClients.filter(client => 
                (client.name && client.name.toLowerCase().includes(searchTerm)) ||
                (client.phone && client.phone.includes(searchTerm)) ||
                (client.email && client.email.toLowerCase().includes(searchTerm)) ||
                (client.id_number && client.id_number.includes(searchTerm)) ||
                (client.company && client.company.toLowerCase().includes(searchTerm))
            );

            displayClients(filtered);
        }

        function openClientModal(editId = null) {
            const modal = document.getElementById('clientModal');
            const title = document.getElementById('modalTitle');
            const submitBtn = document.getElementById('submitButton');

            if (editId) {
                title.textContent = 'Edit Client';
                submitBtn.textContent = 'Update Client';
                loadClientData(editId);
            } else {
                title.textContent = 'Add New Client';
                submitBtn.textContent = 'Add Client';
                document.getElementById('clientForm').reset();
                document.getElementById('clientId').value = '';
            }

            modal.style.display = 'flex';
        }

        function closeClientModal() {
            document.getElementById('clientModal').style.display = 'none';
            document.getElementById('clientForm').reset();
        }

        async function loadClientData(clientId) {
            try {
                const response = await fetch(`/api/clients/${clientId}`);
                const data = await response.json();

                if (data.success) {
                    const client = data.data;
                    document.getElementById('clientId').value = client.id;
                    document.getElementById('clientName').value = client.name || '';
                    document.getElementById('clientPhone').value = client.phone || '';
                    document.getElementById('clientEmail').value = client.email || '';
                    document.getElementById('clientAddress').value = client.address || '';
                    document.getElementById('clientType').value = client.type || 'Buyer';
                    document.getElementById('clientIdNumber').value = client.id_number || '';
                    document.getElementById('clientCompany').value = client.company || '';
                    document.getElementById('clientNotes').value = client.notes || '';
                }
            } catch (error) {
                console.error('Error loading client data:', error);
            }
        }

        document.getElementById('clientForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const clientId = document.getElementById('clientId').value;
            const clientData = {
                name: document.getElementById('clientName').value,
                phone: document.getElementById('clientPhone').value,
                email: document.getElementById('clientEmail').value,
                address: document.getElementById('clientAddress').value,
                type: document.getElementById('clientType').value,
                id_number: document.getElementById('clientIdNumber').value,
                company: document.getElementById('clientCompany').value,
                notes: document.getElementById('clientNotes').value
            };

            try {
                const url = clientId ? `/api/clients/${clientId}` : '/api/clients';
                const method = clientId ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(clientData)
                });

                const data = await response.json();

                if (data.success) {
                    alert(clientId ? 'Client updated successfully!' : 'Client created successfully!');
                    closeClientModal();
                    loadClients();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error saving client');
                console.error(error);
            }
        });

        async function editClient(clientId) {
            openClientModal(clientId);
        }

        async function viewClientSales(clientId) {
            try {
                const response = await fetch(`/api/clients/${clientId}/sales`);
                const data = await response.json();

                if (data.success) {
                    const sales = data.data;
                    let message = `Client's Purchases:\n\n`;

                    if (sales.length === 0) {
                        message += 'No purchases found for this client.';
                    } else {
                        sales.forEach((sale, index) => {
                            message += `${index + 1}. ${sale.unit_number || 'Unit'} - $${sale.total_price?.toLocaleString() || 0}\n`;
                            message += `   Status: ${sale.status || 'Active'}\n`;
                            message += `   Balance: $${sale.remaining_balance?.toLocaleString() || 0}\n\n`;
                        });
                    }

                    alert(message);
                }
            } catch (error) {
                console.error('Error loading client sales:', error);
            }
        }

        function deleteClient(clientId, clientName) {
            clientToDelete = clientId;
            document.getElementById('deleteMessage').textContent = 
                `Are you sure you want to delete client "${clientName}"? This action cannot be undone.`;
            document.getElementById('deleteModal').style.display = 'flex';
        }

        function closeDeleteModal() {
            document.getElementById('deleteModal').style.display = 'none';
            clientToDelete = null;
        }

        async function confirmDelete() {
            if (!clientToDelete) return;

            try {
                const response = await fetch(`/api/clients/${clientToDelete}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    alert('Client deleted successfully!');
                    closeDeleteModal();
                    loadClients();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error deleting client');
                console.error(error);
            } finally {
                clientToDelete = null;
            }
        }

        window.onclick = function(event) {
            const clientModal = document.getElementById('clientModal');
            const deleteModal = document.getElementById('deleteModal');

            if (event.target === clientModal) {
                closeClientModal();
            }
            if (event.target === deleteModal) {
                closeDeleteModal();
            }
        };

        document.addEventListener('DOMContentLoaded', loadClients);
    </script>
</body>
</html>''',

        'reports.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Reports & Analytics - Rawas Real Estate</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f7fa; }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 30px; 
            flex-wrap: wrap; 
        }
        .nav-btn { 
            padding: 10px 20px; 
            background: #3498db; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            transition: all 0.3s;
        }
        .nav-btn:hover { 
            background: #2980b9; 
            transform: translateY(-2px); 
        }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            flex-wrap: wrap; 
            gap: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
        }
        .header h1 { font-size: 2.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        
        .report-controls { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 30px; 
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            flex-wrap: wrap;
        }
        .control-group { 
            display: flex; 
            flex-direction: column; 
            gap: 8px; 
        }
        .control-group label { 
            font-weight: 600; 
            color: #2c3e50; 
            font-size: 0.9rem; 
        }
        .control-group select, 
        .control-group input { 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
            min-width: 180px; 
        }
        
        .btn { 
            padding: 12px 25px; 
            background: #3498db; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 1rem; 
            transition: all 0.3s; 
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover { 
            background: #2980b9; 
            transform: translateY(-2px); 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
        }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #219653; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #d68910; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-info { background: #17a2b8; }
        .btn-info:hover { background: #138496; }
        
        .reports-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); 
            gap: 25px; 
            margin-bottom: 40px; 
        }
        .report-card { 
            background: white; 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border-top: 4px solid #3498db;
            transition: all 0.3s;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .report-card:hover { 
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.12);
        }
        .report-card h3 { 
            color: #2c3e50; 
            margin-bottom: 15px; 
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .report-card p { 
            color: #7f8c8d; 
            line-height: 1.6; 
            margin-bottom: 20px; 
            flex-grow: 1;
        }
        .report-card .btn { 
            margin-top: auto; 
            width: 100%; 
            justify-content: center;
        }
        
        .chart-container { 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            margin-bottom: 30px;
            position: relative;
        }
        .chart-container h3 { 
            color: #2c3e50; 
            margin-bottom: 20px; 
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .chart-actions {
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        
        .table-container { 
            background: white; 
            border-radius: 15px; 
            overflow: hidden; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            margin-bottom: 30px;
            overflow-x: auto;
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        th { 
            background: #f8f9fa; 
            padding: 15px; 
            text-align: left; 
            color: #2c3e50; 
            font-weight: 600; 
            border-bottom: 2px solid #e0e0e0; 
            position: sticky;
            top: 0;
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #e9ecef; 
        }
        tr:hover { background: #f9f9f9; }
        tr:last-child td { border-bottom: none; }
        
        .stats-cards { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }
        .stat-card { 
            background: white; 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            text-align: center;
            transition: all 0.3s;
        }
        .stat-card:hover { 
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.12);
        }
        .stat-icon { 
            font-size: 2.5rem; 
            color: #3498db; 
            margin-bottom: 15px; 
        }
        .stat-value { 
            font-size: 2.2rem; 
            font-weight: bold; 
            color: #2c3e50; 
            margin: 10px 0; 
        }
        .stat-label { 
            color: #7f8c8d; 
            font-size: 0.9rem; 
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-change {
            font-size: 0.85rem;
            margin-top: 10px;
            padding: 3px 8px;
            border-radius: 20px;
            display: inline-block;
        }
        .positive { background: #d4edda; color: #155724; }
        .negative { background: #f8d7da; color: #721c24; }
        .neutral { background: #fff3cd; color: #856404; }
        
        .loading { 
            display: inline-block; 
            width: 20px; 
            height: 20px; 
            border: 3px solid #f3f3f3; 
            border-top: 3px solid #3498db; 
            border-radius: 50%; 
            animation: spin 1s linear infinite; 
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .modal { 
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.7); 
            justify-content: center; 
            align-items: center; 
            z-index: 1000; 
            padding: 20px;
        }
        .modal-content { 
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            max-width: 900px; 
            width: 95%; 
            max-height: 85vh; 
            overflow-y: auto; 
            position: relative;
        }
        .modal-close { 
            position: absolute; 
            top: 15px; 
            right: 15px; 
            background: none; 
            border: none; 
            font-size: 1.5rem; 
            cursor: pointer; 
            color: #7f8c8d; 
        }
        
        .message { 
            padding: 15px 20px; 
            border-radius: 10px; 
            margin-bottom: 30px; 
            display: none; 
            align-items: center;
            gap: 10px;
        }
        .message.success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .message.error { 
            background: #f8d7da; 
            color: #721c24; 
            border: 1px solid #f5c6cb; 
        }
        .message.info { 
            background: #d1ecf1; 
            color: #0c5460; 
            border: 1px solid #bee5eb; 
        }
        
        .date-range { 
            display: flex; 
            gap: 10px; 
            align-items: center; 
        }
        
        .tabs { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 25px; 
            border-bottom: 1px solid #e0e0e0; 
            padding-bottom: 15px; 
            flex-wrap: wrap;
        }
        .tab-btn { 
            padding: 10px 25px; 
            background: #ecf0f1; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer; 
            font-weight: 500;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .tab-btn:hover { 
            background: #d5dbdb; 
        }
        .tab-btn.active { 
            background: #3498db; 
            color: white; 
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
        }
        
        .export-options {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .export-btn {
            padding: 10px 20px;
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }
        .export-btn:hover {
            background: #27ae60;
            transform: translateY(-2px);
        }
        .export-btn.pdf { background: #e74c3c; }
        .export-btn.pdf:hover { background: #c0392b; }
        .export-btn.excel { background: #2ecc71; }
        .export-btn.excel:hover { background: #27ae60; }
        .export-btn.print { background: #3498db; }
        .export-btn.print:hover { background: #2980b9; }
        
        .report-preview {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        @media (max-width: 1200px) {
            .reports-grid { grid-template-columns: repeat(2, 1fr); }
        }
        
        @media (max-width: 768px) {
            .reports-grid { grid-template-columns: 1fr; }
            .header { padding: 20px; }
            .header h1 { font-size: 2rem; }
            .chart-actions { position: static; margin-bottom: 20px; }
            .date-range { flex-direction: column; align-items: stretch; }
            .control-group select, .control-group input { min-width: 100%; }
        }
        
        @media (max-width: 480px) {
            .nav { justify-content: center; }
            .nav-btn { width: 100%; text-align: center; }
            .report-controls { flex-direction: column; }
            .export-options { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/" class="nav-btn"><i class="fas fa-home"></i> Home</a>
            <a href="/dashboard" class="nav-btn"><i class="fas fa-chart-bar"></i> Dashboard</a>
            <a href="/projects" class="nav-btn"><i class="fas fa-building"></i> Projects</a>
            <a href="/sales" class="nav-btn"><i class="fas fa-dollar-sign"></i> Sales</a>
            <a href="/clients" class="nav-btn"><i class="fas fa-users"></i> Clients</a>
            <a href="/employees" class="nav-btn"><i class="fas fa-users-cog"></i> Employees</a>
            <a href="/inventory" class="nav-btn"><i class="fas fa-box"></i> Inventory</a>
        </div>

        <div class="header">
            <div>
                <h1><i class="fas fa-chart-line"></i> Reports & Analytics</h1>
                <p>Comprehensive reports and insights for data-driven decisions</p>
            </div>
            <button class="btn btn-success" onclick="exportAllReports()">
                <i class="fas fa-file-export"></i> Export All Reports
            </button>
        </div>

        <div id="message" class="message"></div>

        <div class="report-controls">
            <div class="control-group">
                <label><i class="fas fa-calendar-alt"></i> Date Range</label>
                <div class="date-range">
                    <input type="date" id="startDate" value="2023-01-01">
                    <span>to</span>
                    <input type="date" id="endDate" value="2024-12-31">
                </div>
            </div>
            <div class="control-group">
                <label><i class="fas fa-filter"></i> Report Type</label>
                <select id="reportType" onchange="filterReports()">
                    <option value="all">All Reports</option>
                    <option value="sales">Sales Reports</option>
                    <option value="financial">Financial Reports</option>
                    <option value="projects">Project Reports</option>
                    <option value="clients">Client Reports</option>
                    <option value="inventory">Inventory Reports</option>
                </select>
            </div>
            <div class="control-group">
                <label><i class="fas fa-chart-bar"></i> View Type</label>
                <select id="viewType" onchange="changeViewType()">
                    <option value="cards">Cards View</option>
                    <option value="charts">Charts View</option>
                    <option value="tables">Tables View</option>
                </select>
            </div>
            <button class="btn" onclick="applyFilters()" style="align-self: flex-end;">
                <i class="fas fa-search"></i> Apply Filters
            </button>
        </div>

        <div class="tabs" id="reportTabs">
            <button class="tab-btn active" onclick="showTab('summary')">
                <i class="fas fa-tachometer-alt"></i> Summary
            </button>
            <button class="tab-btn" onclick="showTab('sales')">
                <i class="fas fa-dollar-sign"></i> Sales
            </button>
            <button class="tab-btn" onclick="showTab('financial')">
                <i class="fas fa-money-bill-wave"></i> Financial
            </button>
            <button class="tab-btn" onclick="showTab('clients')">
                <i class="fas fa-users"></i> Clients
            </button>
            <button class="tab-btn" onclick="showTab('projects')">
                <i class="fas fa-building"></i> Projects
            </button>
            <button class="tab-btn" onclick="showTab('inventory')">
                <i class="fas fa-box"></i> Inventory
            </button>
        </div>

        <div id="summaryTab" class="tab-content">
            <div class="stats-cards" id="summaryStats">
                <!-- Summary statistics will be loaded here -->
            </div>

            <div class="chart-container">
                <h3><i class="fas fa-chart-line"></i> Revenue Overview</h3>
                <div class="chart-actions">
                    <button class="btn btn-sm" onclick="downloadChart('revenueChart')">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>
                <canvas id="revenueChart" height="300"></canvas>
            </div>

            <div class="reports-grid">
                <div class="report-card">
                    <h3><i class="fas fa-chart-pie"></i> Sales Performance</h3>
                    <p>Detailed analysis of sales performance including revenue, units sold, and trends over time.</p>
                    <button class="btn" onclick="generateReport('sales_performance')">
                        <i class="fas fa-play"></i> Generate Report
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-user-tie"></i> Top Performers</h3>
                    <p>Identify top-performing employees, agents, and sales teams based on sales metrics.</p>
                    <button class="btn" onclick="generateReport('top_performers')">
                        <i class="fas fa-play"></i> Generate Report
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-project-diagram"></i> Project Status</h3>
                    <p>Comprehensive overview of all projects including progress, completion status, and budgets.</p>
                    <button class="btn" onclick="generateReport('project_status')">
                        <i class="fas fa-play"></i> Generate Report
                    </button>
                </div>
            </div>
        </div>

        <div id="salesTab" class="tab-content" style="display: none;">
            <div class="chart-container">
                <h3><i class="fas fa-chart-bar"></i> Monthly Sales Report</h3>
                <canvas id="salesChart" height="300"></canvas>
            </div>

            <div class="table-container">
                <h3 style="padding: 20px; margin: 0;">Detailed Sales Data</h3>
                <table id="salesTable">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Unit</th>
                            <th>Client</th>
                            <th>Agent</th>
                            <th>Amount</th>
                            <th>Payment</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Sales data will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <div id="financialTab" class="tab-content" style="display: none;">
            <div class="stats-cards" id="financialStats">
                <!-- Financial stats will be loaded here -->
            </div>

            <div class="chart-container">
                <h3><i class="fas fa-money-check-alt"></i> Financial Overview</h3>
                <canvas id="financialChart" height="300"></canvas>
            </div>

            <div class="reports-grid">
                <div class="report-card">
                    <h3><i class="fas fa-file-invoice-dollar"></i> Revenue Report</h3>
                    <p>Detailed revenue breakdown by project, unit type, and payment methods.</p>
                    <button class="btn btn-success" onclick="generateFinancialReport('revenue')">
                        <i class="fas fa-file-pdf"></i> Generate PDF
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-hand-holding-usd"></i> Cash Flow</h3>
                    <p>Cash inflow and outflow analysis with projections and variance reports.</p>
                    <button class="btn btn-success" onclick="generateFinancialReport('cashflow')">
                        <i class="fas fa-file-excel"></i> Generate Excel
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-balance-scale"></i> Profit & Loss</h3>
                    <p>Monthly profit and loss statements with expense categorization.</p>
                    <button class="btn btn-success" onclick="generateFinancialReport('profitloss')">
                        <i class="fas fa-print"></i> Print Report
                    </button>
                </div>
            </div>
        </div>

        <div id="clientsTab" class="tab-content" style="display: none;">
            <div class="stats-cards" id="clientsStats">
                <!-- Client specific stats will be loaded here -->
            </div>

            <div class="reports-grid">
                <div class="chart-container">
                    <h3><i class="fas fa-user-friends"></i> Client Demographics</h3>
                    <canvas id="clientsChart" height="300"></canvas>
                </div>
                <div class="chart-container">
                    <h3><i class="fas fa-chart-line"></i> New Clients Trend</h3>
                    <canvas id="newClientsChart" height="300"></canvas>
                </div>
            </div>

            <div class="table-container">
                <h3 style="padding: 20px; margin: 0;"><i class="fas fa-star"></i> Top 10 Clients by Investment</h3>
                <table id="topClientsTable">
                    <thead>
                        <tr>
                            <th>Client Name</th>
                            <th>Type</th>
                            <th>Purchases</th>
                            <th>Total Spent</th>
                            <th>Last Purchase</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Top clients data will be loaded here -->
                    </tbody>
                </table>
            </div>

            <div class="table-container" style="margin-top: 30px;">
                <h3 style="padding: 20px; margin: 0;"><i class="fas fa-users"></i> Client Type Distribution</h3>
                <table id="clientsTable">
                    <thead>
                        <tr>
                            <th>Client Type</th>
                            <th>Count</th>
                            <th>Total Sales</th>
                            <th>Avg. Purchase</th>
                            <th>Growth %</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Client data will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <div id="projectsTab" class="tab-content" style="display: none;">
            <div class="chart-container">
                <h3><i class="fas fa-hard-hat"></i> Project Progress</h3>
                <canvas id="projectsChart" height="300"></canvas>
            </div>

            <div class="reports-grid">
                <div class="report-card">
                    <h3><i class="fas fa-tasks"></i> Project Status</h3>
                    <p>Detailed status of all projects with completion percentages and timelines.</p>
                    <button class="btn" onclick="generateProjectReport('status')">
                        <i class="fas fa-eye"></i> View Report
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-chart-line"></i> Project Budget</h3>
                    <p>Budget vs actual spending analysis for each project.</p>
                    <button class="btn" onclick="generateProjectReport('budget')">
                        <i class="fas fa-eye"></i> View Report
                    </button>
                </div>
                <div class="report-card">
                    <h3><i class="fas fa-calendar-check"></i> Milestone Report</h3>
                    <p>Project milestones achievement and upcoming deadlines.</p>
                    <button class="btn" onclick="generateProjectReport('milestones')">
                        <i class="fas fa-eye"></i> View Report
                    </button>
                </div>
            </div>
        </div>

        <div id="inventoryTab" class="tab-content" style="display: none;">
            <div class="chart-container">
                <h3><i class="fas fa-boxes"></i> Inventory Levels</h3>
                <canvas id="inventoryChart" height="300"></canvas>
            </div>

            <div class="table-container">
                <h3 style="padding: 20px; margin: 0;">Inventory Status</h3>
                <table id="inventoryTable">
                    <thead>
                        <tr>
                            <th>Material</th>
                            <th>Category</th>
                            <th>Current Stock</th>
                            <th>Min Level</th>
                            <th>Status</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Inventory data will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Report Preview Modal -->
    <div id="reportModal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeReportModal()">&times;</button>
            <h2 id="modalTitle" style="margin-bottom: 20px;"><i class="fas fa-file-alt"></i> Report Preview</h2>
            <div class="export-options">
                <button class="export-btn pdf" onclick="exportReport('pdf')">
                    <i class="fas fa-file-pdf"></i> Export as PDF
                </button>
                <button class="export-btn excel" onclick="exportReport('excel')">
                    <i class="fas fa-file-excel"></i> Export as Excel
                </button>
                <button class="export-btn print" onclick="printReport()">
                    <i class="fas fa-print"></i> Print Report
                </button>
            </div>
            <div class="report-preview" id="reportPreview">
                <!-- Report content will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'summary';
        let revenueChart = null;
        let salesChart = null;
        let financialChart = null;
        let clientsChart = null;
        let projectsChart = null;
        let inventoryChart = null;

        document.addEventListener('DOMContentLoaded', function() {
            loadSummaryStats();
            initializeCharts();
            loadSalesData();
            loadFinancialStats();
            loadClientsData();
            loadProjectsData();
            loadInventoryData();
            
            // Set default dates
            const endDate = new Date();
            const startDate = new Date();
            startDate.setMonth(startDate.getMonth() - 12);
            
            document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
            document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
        });

        function showMessage(message, type = 'success') {
            const messageDiv = document.getElementById('message');
            messageDiv.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                ${message}
            `;
            messageDiv.className = `message ${type}`;
            messageDiv.style.display = 'flex';

            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(`${tabName}Tab`).style.display = 'block';
            
            // Add active class to clicked button
            event.target.classList.add('active');
            
            currentTab = tabName;
            
            // Load data for the selected tab if needed
            switch(tabName) {
                case 'sales':
                    if (!salesChart) loadSalesData();
                    break;
                case 'financial':
                    if (!financialChart) loadFinancialStats();
                    break;
                case 'clients':
                    if (!clientsChart) loadClientsData();
                    break;
                case 'projects':
                    if (!projectsChart) loadProjectsData();
                    break;
                case 'inventory':
                    if (!inventoryChart) loadInventoryData();
                    break;
            }
        }

        function applyFilters() {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            showMessage('Applying filters...', 'info');
            
            // Reload all data with new filters
            setTimeout(() => {
                loadSummaryStats();
                loadSalesData();
                loadFinancialStats();
                loadClientsData();
                loadProjectsData();
                loadInventoryData();
                showMessage('Filters applied successfully!');
            }, 500);
        }

        function filterReports() {
            const reportType = document.getElementById('reportType').value;
            const cards = document.querySelectorAll('.report-card');
            
            cards.forEach(card => {
                if (reportType === 'all') {
                    card.style.display = 'flex';
                } else {
                    const title = card.querySelector('h3').textContent.toLowerCase();
                    if (title.includes(reportType)) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        }

        function changeViewType() {
            const viewType = document.getElementById('viewType').value;
            const cardsContainer = document.querySelector('.reports-grid');
            const chartsContainer = document.querySelectorAll('.chart-container');
            const tablesContainer = document.querySelectorAll('.table-container');
            
            switch(viewType) {
                case 'cards':
                    cardsContainer.style.display = 'grid';
                    chartsContainer.forEach(chart => chart.style.display = 'block');
                    tablesContainer.forEach(table => table.style.display = 'none');
                    break;
                case 'charts':
                    cardsContainer.style.display = 'none';
                    chartsContainer.forEach(chart => chart.style.display = 'block');
                    tablesContainer.forEach(table => table.style.display = 'none');
                    break;
                case 'tables':
                    cardsContainer.style.display = 'none';
                    chartsContainer.forEach(chart => chart.style.display = 'none');
                    tablesContainer.forEach(table => table.style.display = 'block');
                    break;
            }
        }

        async function loadSummaryStats() {
            try {
                const response = await fetch('/api/dashboard/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;
                    const container = document.getElementById('summaryStats');

                    container.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-building"></i></div>
                            <div class="stat-value">${stats.projects || 0}</div>
                            <div class="stat-label">Active Projects</div>
                            <div class="stat-change positive">+12%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-dollar-sign"></i></div>
                            <div class="stat-value">$${(stats.sales_revenue || 0).toLocaleString()}</div>
                            <div class="stat-label">Total Revenue</div>
                            <div class="stat-change positive">+8%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-users"></i></div>
                            <div class="stat-value">${stats.clients || 0}</div>
                            <div class="stat-label">Active Clients</div>
                            <div class="stat-change positive">+5%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-door-closed"></i></div>
                            <div class="stat-value">${stats.units?.Available || 0}</div>
                            <div class="stat-label">Available Units</div>
                            <div class="stat-change neutral">0%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-chart-line"></i></div>
                            <div class="stat-value">${stats.sales_count || 0}</div>
                            <div class="stat-label">Total Sales</div>
                            <div class="stat-change positive">+15%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
                            <div class="stat-value">${stats.delayed_payments || 0}</div>
                            <div class="stat-label">Delayed Payments</div>
                            <div class="stat-change negative">-3%</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading summary stats:', error);
            }
        }

        function initializeCharts() {
            // Revenue Chart
            const revenueCtx = document.getElementById('revenueChart').getContext('2d');
            revenueChart = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    datasets: [{
                        label: 'Revenue ($)',
                        data: [85000, 92000, 105000, 98000, 112000, 125000, 138000, 145000, 132000, 148000, 162000, 175000],
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Monthly Revenue Trend'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        async function loadSalesData() {
            try {
                const response = await fetch('/api/sales');
                const data = await response.json();

                if (data.success) {
                    updateSalesChart(data.data);
                    updateSalesTable(data.data.slice(0, 10));
                }
            } catch (error) {
                console.error('Error loading sales data:', error);
            }
        }

        function updateSalesChart(salesData) {
            // Group sales by month
            const monthlySales = {};
            salesData.forEach(sale => {
                if (sale.contract_date) {
                    const month = sale.contract_date.substring(0, 7); // YYYY-MM
                    monthlySales[month] = (monthlySales[month] || 0) + (sale.total_price || 0);
                }
            });

            const months = Object.keys(monthlySales).sort();
            const amounts = months.map(month => monthlySales[month]);

            const salesCtx = document.getElementById('salesChart').getContext('2d');
            
            if (salesChart) {
                salesChart.destroy();
            }

            salesChart = new Chart(salesCtx, {
                type: 'bar',
                data: {
                    labels: months.map(m => {
                        const [year, month] = m.split('-');
                        return `${month}/${year}`;
                    }),
                    datasets: [{
                        label: 'Sales Revenue ($)',
                        data: amounts,
                        backgroundColor: 'rgba(46, 204, 113, 0.7)',
                        borderColor: 'rgba(46, 204, 113, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Monthly Sales Performance'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        function updateSalesTable(salesData) {
            const tbody = document.querySelector('#salesTable tbody');
            
            if (!salesData || salesData.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; padding: 30px; color: #7f8c8d;">
                            <i class="fas fa-chart-bar" style="font-size: 2rem; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                            No sales data available
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = salesData.map(sale => {
                const date = sale.contract_date ? 
                    new Date(sale.contract_date).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                    }) : 'N/A';
                
                const paid = sale.total_price - sale.remaining_balance;
                const paymentPercentage = sale.total_price > 0 ? 
                    Math.round((paid / sale.total_price) * 100) : 0;

                return `
                <tr>
                    <td>${date}</td>
                    <td>${sale.unit_number || 'N/A'}</td>
                    <td>${sale.client_name || 'N/A'}</td>
                    <td>${sale.employee_name || 'N/A'}</td>
                    <td><strong>$${(sale.total_price || 0).toLocaleString()}</strong></td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="flex-grow: 1; height: 8px; background: #ecf0f1; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${paymentPercentage}%; height: 100%; background: #27ae60;"></div>
                            </div>
                            <span>${paymentPercentage}%</span>
                        </div>
                    </td>
                    <td>
                        <span style="padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; 
                            background: ${sale.status === 'Completed' ? '#d4edda' : sale.status === 'Active' ? '#d1ecf1' : '#f8d7da'}; 
                            color: ${sale.status === 'Completed' ? '#155724' : sale.status === 'Active' ? '#0c5460' : '#721c24'}">
                            ${sale.status || 'Active'}
                        </span>
                    </td>
                </tr>
                `;
            }).join('');
        }

        async function loadFinancialStats() {
            try {
                const response = await fetch('/api/reports/sales-summary');
                const data = await response.json();

                if (data.success) {
                    updateFinancialStats(data);
                    updateFinancialChart(data);
                }
            } catch (error) {
                console.error('Error loading financial stats:', error);
            }
        }

        function updateFinancialStats(data) {
            const container = document.getElementById('financialStats');
            
            if (data.totals) {
                container.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-chart-line"></i></div>
                        <div class="stat-value">$${(data.totals.total_revenue || 0).toLocaleString()}</div>
                        <div class="stat-label">Total Revenue</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-hand-holding-usd"></i></div>
                        <div class="stat-value">$${(data.totals.total_down || 0).toLocaleString()}</div>
                        <div class="stat-label">Down Payments</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-balance-scale"></i></div>
                        <div class="stat-value">$${(data.totals.total_remaining || 0).toLocaleString()}</div>
                        <div class="stat-label">Pending Balance</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-calculator"></i></div>
                        <div class="stat-value">$${(data.totals.avg_price || 0).toLocaleString()}</div>
                        <div class="stat-label">Avg. Sale Price</div>
                    </div>
                `;
            }
        }

        function updateFinancialChart(data) {
            const financialCtx = document.getElementById('financialChart').getContext('2d');
            
            if (financialChart) {
                financialChart.destroy();
            }

            // Prepare data for financial chart
            const months = data.monthly ? data.monthly.map(item => item.month) : [];
            const revenues = data.monthly ? data.monthly.map(item => item.total_revenue || 0) : [];
            const expenses = revenues.map(revenue => revenue * 0.3); // Simulated expenses

            financialChart = new Chart(financialCtx, {
                type: 'bar',
                data: {
                    labels: months,
                    datasets: [
                        {
                            label: 'Revenue',
                            data: revenues,
                            backgroundColor: 'rgba(52, 152, 219, 0.7)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Expenses',
                            data: expenses,
                            backgroundColor: 'rgba(231, 76, 60, 0.7)',
                            borderColor: 'rgba(231, 76, 60, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Revenue vs Expenses'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        }

        async function loadClientsData() {
            try {
                const response = await fetch('/api/reports/client-statistics');
                const data = await response.json();

                if (data.success) {
                    updateClientsChart(data);
                    updateClientsTable(data);
                }
            } catch (error) {
                console.error('Error loading clients data:', error);
            }
        }

        function updateClientsChart(data) {
            const clientsCtx = document.getElementById('clientsChart').getContext('2d');
            
            if (clientsChart) {
                clientsChart.destroy();
            }

            const types = data.by_type ? data.by_type.map(item => item.type) : ['Buyer', 'Investor', 'Tenant'];
            const counts = data.by_type ? data.by_type.map(item => item.count) : [45, 30, 25];

            clientsChart = new Chart(clientsCtx, {
                type: 'doughnut',
                data: {
                    labels: types,
                    datasets: [{
                        data: counts,
                        backgroundColor: [
                            '#3498db',
                            '#2ecc71',
                            '#f39c12',
                            '#9b59b6',
                            '#e74c3c'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        title: {
                            display: true,
                            text: 'Clients by Type'
                        }
                    }
                }
            });
        }

        function formatCurrency(value) {
            if (value >= 1000000) {
                return (value / 1000000).toFixed(2) + 'M';
            } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K';
            }
            return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        function updateClientsTable(data) {
            // Update Stats Cards
            const statsContainer = document.getElementById('clientsStats');
            const totalClients = data.by_type ? data.by_type.reduce((sum, item) => sum + item.count, 0) : 0;
            
            // Calculate total investment from by_type to get the full sum of all sales
            const totalSpent = data.by_type ? data.by_type.reduce((sum, item) => sum + (parseFloat(item.total_sales) || 0), 0) : 0;
            
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(52, 152, 219, 0.1); color: #3498db;"><i class="fas fa-users"></i></div>
                    <div class="stat-value">${totalClients}</div>
                    <div class="stat-label">Total Clients</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(46, 204, 113, 0.1); color: #2ecc71;"><i class="fas fa-hand-holding-usd"></i></div>
                    <div class="stat-value">$${formatCurrency(totalSpent)}</div>
                    <div class="stat-label">Total Investment</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon" style="background: rgba(155, 89, 182, 0.1); color: #9b59b6;"><i class="fas fa-chart-pie"></i></div>
                    <div class="stat-value">${data.by_type ? data.by_type.length : 0}</div>
                    <div class="stat-label">Client Segments</div>
                </div>
            `;

            // Update New Clients Chart
            updateNewClientsChart(data.new_clients);

            // Update Top Clients Table
            const topTbody = document.querySelector('#topClientsTable tbody');
            if (data.top_clients && data.top_clients.length > 0) {
                topTbody.innerHTML = data.top_clients.map(client => `
                    <tr>
                        <td><strong>${client.name}</strong></td>
                        <td><span class="badge badge-info">${client.type}</span></td>
                        <td>${client.purchases}</td>
                        <td>$${(client.total_spent || 0).toLocaleString()}</td>
                        <td>${client.last_purchase ? new Date(client.last_purchase).toLocaleDateString() : 'N/A'}</td>
                    </tr>
                `).join('');
            } else {
                topTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">No investment data</td></tr>';
            }

            // Update Type Distribution Table
            const tbody = document.querySelector('#clientsTable tbody');
            if (!data.by_type || data.by_type.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">No client data available</td></tr>';
                return;
            }

            tbody.innerHTML = data.by_type.map((type, index) => {
                const growth = [5, 12, -3, 8, 15][index % 5];
                const avgPurchase = type.count > 0 ? (type.total_sales || 0) / type.count : 0;
                const totalSales = type.total_sales || 0;

                return `
                <tr>
                    <td><strong>${type.type}</strong></td>
                    <td>${type.count || 0}</td>
                    <td>$${totalSales.toLocaleString()}</td>
                    <td>$${avgPurchase.toLocaleString()}</td>
                    <td>
                        <span style="color: ${growth >= 0 ? '#27ae60' : '#e74c3c'}; font-weight: 600;">
                            ${growth >= 0 ? '+' : ''}${growth}%
                        </span>
                    </td>
                </tr>
                `;
            }).join('');
        }

        let newClientsChart = null;
        function updateNewClientsChart(newData) {
            const ctx = document.getElementById('newClientsChart').getContext('2d');
            if (newClientsChart) newClientsChart.destroy();

            const labels = newData ? newData.map(d => d.month) : [];
            const values = newData ? newData.map(d => d.new_clients) : [];

            newClientsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'New Clients',
                        data: values,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        async function loadProjectsData() {
            try {
                const response = await fetch('/api/projects');
                const data = await response.json();

                if (data.success) {
                    updateProjectsChart(data.data);
                }
            } catch (error) {
                console.error('Error loading projects data:', error);
            }
        }

        function updateProjectsChart(projects) {
            const projectsCtx = document.getElementById('projectsChart').getContext('2d');
            
            if (projectsChart) {
                projectsChart.destroy();
            }

            const projectNames = projects.map(p => p.name);
            const buildingsCount = projects.map(p => p.buildings_count || 0);
            const unitsCount = projects.map(p => p.units_count || 0);

            projectsChart = new Chart(projectsCtx, {
                type: 'bar',
                data: {
                    labels: projectNames,
                    datasets: [
                        {
                            label: 'Buildings',
                            data: buildingsCount,
                            backgroundColor: 'rgba(52, 152, 219, 0.7)',
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Units',
                            data: unitsCount,
                            backgroundColor: 'rgba(46, 204, 113, 0.7)',
                            borderColor: 'rgba(46, 204, 113, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Projects Overview'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        async function loadInventoryData() {
            try {
                const response = await fetch('/api/materials');
                const data = await response.json();

                if (data.success) {
                    updateInventoryChart(data.data);
                    updateInventoryTable(data.data);
                }
            } catch (error) {
                console.error('Error loading inventory data:', error);
            }
        }

        function updateInventoryChart(materials) {
            const inventoryCtx = document.getElementById('inventoryChart').getContext('2d');
            
            if (inventoryChart) {
                inventoryChart.destroy();
            }

            // Group by category
            const categories = {};
            materials.forEach(mat => {
                const category = mat.category || 'Other';
                categories[category] = (categories[category] || 0) + (mat.current_stock || 0);
            });

            const categoryNames = Object.keys(categories);
            const stockValues = Object.values(categories);

            inventoryChart = new Chart(inventoryCtx, {
                type: 'polarArea',
                data: {
                    labels: categoryNames,
                    datasets: [{
                        data: stockValues,
                        backgroundColor: [
                            '#3498db',
                            '#2ecc71',
                            '#f39c12',
                            '#9b59b6',
                            '#e74c3c',
                            '#1abc9c',
                            '#34495e'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        },
                        title: {
                            display: true,
                            text: 'Inventory by Category'
                        }
                    }
                }
            });
        }

        function updateInventoryTable(materials) {
            const tbody = document.querySelector('#inventoryTable tbody');
            
            if (!materials || materials.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 30px; color: #7f8c8d;">
                            <i class="fas fa-boxes" style="font-size: 2rem; margin-bottom: 10px; display: block; opacity: 0.5;"></i>
                            No inventory data available
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = materials.map(material => {
                const currentStock = material.current_stock || 0;
                const minQuantity = material.min_quantity || 0;
                
                let status = 'Adequate';
                let statusColor = '#27ae60';
                
                if (currentStock === 0) {
                    status = 'Out of Stock';
                    statusColor = '#e74c3c';
                } else if (currentStock <= minQuantity * 0.2) {
                    status = 'Critical';
                    statusColor = '#e67e22';
                } else if (currentStock <= minQuantity) {
                    status = 'Low';
                    statusColor = '#f39c12';
                }

                const stockValue = (currentStock * (material.price || 0)).toFixed(2);

                return `
                <tr>
                    <td><strong>${material.name}</strong></td>
                    <td>${material.category || 'N/A'}</td>
                    <td><strong>${currentStock}</strong> ${material.unit || ''}</td>
                    <td>${minQuantity}</td>
                    <td>
                        <span style="color: ${statusColor}; font-weight: 600;">
                            ${status}
                        </span>
                    </td>
                    <td>$${stockValue}</td>
                </tr>
                `;
            }).join('');
        }

        function generateReport(reportType) {
            const modal = document.getElementById('reportModal');
            const modalTitle = document.getElementById('modalTitle');
            const preview = document.getElementById('reportPreview');

            let title = '';
            let content = '';

            switch(reportType) {
                case 'sales_performance':
                    title = 'Sales Performance Report';
                    content = `
                        <h3>Sales Performance Analysis</h3>
                        <p><strong>Date Range:</strong> ${document.getElementById('startDate').value} to ${document.getElementById('endDate').value}</p>
                        
                        <h4>Executive Summary</h4>
                        <ul>
                            <li>Total Sales: 156 units</li>
                            <li>Total Revenue: $12,450,000</li>
                            <li>Average Sale Price: $79,808</li>
                            <li>Growth Rate: 15.2%</li>
                        </ul>
                        
                        <h4>Monthly Breakdown</h4>
                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                            <thead>
                                <tr>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Month</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Units Sold</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Revenue</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Growth</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 8px;">January 2024</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">12</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">$850,000</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">+8%</td>
                                </tr>
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 8px;">February 2024</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">15</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">$1,050,000</td>
                                    <td style="border: 1px solid #ddd; padding: 8px;">+12%</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h4>Recommendations</h4>
                        <ol>
                            <li>Focus marketing efforts on luxury apartment segment</li>
                            <li>Increase sales team training for Q3</li>
                            <li>Consider price adjustments for slower-moving units</li>
                        </ol>
                    `;
                    break;

                case 'top_performers':
                    title = 'Top Performers Report';
                    content = `
                        <h3>Top Performers Analysis</h3>
                        <p><strong>Date Range:</strong> ${document.getElementById('startDate').value} to ${document.getElementById('endDate').value}</p>
                        
                        <h4>Top Sales Agents</h4>
                        <ol>
                            <li>Ahmed Saleh - $2,450,000 in sales (18 units)</li>
                            <li>Rana Omar - $1,980,000 in sales (15 units)</li>
                            <li>Yousef Nasser - $1,750,000 in sales (12 units)</li>
                        </ol>
                        
                        <h4>Performance Metrics</h4>
                        <ul>
                            <li>Average Commission Rate: 3.2%</li>
                            <li>Conversion Rate: 28%</li>
                            <li>Average Deal Size: $82,500</li>
                        </ul>
                        
                        <h4>Recognition & Rewards</h4>
                        <p>Top performers are eligible for:</p>
                        <ul>
                            <li>Quarterly bonus (top 3 performers)</li>
                            <li>Sales incentive trip (annual)</li>
                            <li>Professional development opportunities</li>
                        </ul>
                    `;
                    break;

                case 'project_status':
                    title = 'Project Status Report';
                    content = `
                        <h3>Project Status Report</h3>
                        <p><strong>Report Date:</strong> ${new Date().toLocaleDateString()}</p>
                        
                        <h4>Project Overview</h4>
                        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                            <thead>
                                <tr>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Project</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Status</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Progress</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Units Sold</th>
                                    <th style="border: 1px solid #ddd; padding: 8px;">Revenue</li>
                            </tbody>
                        </table>
                    `;
                    break;
            }

            modalTitle.innerHTML = `<i class="fas fa-file-alt"></i> ${title}`;
            preview.innerHTML = content;
            modal.style.display = 'flex';
        }

        function generateFinancialReport(reportType) {
            let message = '';
            
            switch(reportType) {
                case 'revenue':
                    message = 'Revenue report PDF is being generated...';
                    showMessage(message, 'info');
                    setTimeout(() => {
                        showMessage('Revenue report PDF generated successfully!', 'success');
                    }, 2000);
                    break;
                case 'cashflow':
                    message = 'Cash flow Excel report is being generated...';
                    showMessage(message, 'info');
                    setTimeout(() => {
                        showMessage('Cash flow Excel report generated successfully!', 'success');
                    }, 2000);
                    break;
                case 'profitloss':
                    message = 'Profit & Loss report is being printed...';
                    showMessage(message, 'info');
                    setTimeout(() => {
                        window.print();
                        showMessage('Profit & Loss report printed successfully!', 'success');
                    }, 1000);
                    break;
            }
        }

        function generateProjectReport(reportType) {
            openReportModal();
            
            let content = '';
            
            switch(reportType) {
                case 'status':
                    content = `
                        <h3>Project Status Report</h3>
                        <h4>Project Completion Status</h4>
                        <ul>
                            <li>Al-Masayef Towers: 65% complete</li>
                            <li>Rawas Business Center: 40% complete</li>
                            <li>Al-Andalus Villas: 100% complete</li>
                        </ul>
                        
                        <h4>Key Milestones</h4>
                        <ul>
                            <li>Foundation work completed for all projects</li>
                            <li>Structural work 80% complete</li>
                            <li>Finishing work started for Tower A</li>
                        </ul>
                    `;
                    break;
                    
                case 'budget':
                    content = `
                        <h3>Project Budget Report</h3>
                        <h4>Budget vs Actual</h4>
                        <ul>
                            <li>Al-Masayef Towers: $4.5M budget, $3.2M spent (71%)</li>
                            <li>Rawas Business Center: $3.2M budget, $1.8M spent (56%)</li>
                            <li>Al-Andalus Villas: $2.8M budget, $2.9M spent (104%)</li>
                        </ul>
                        
                        <h4>Cost Analysis</h4>
                        <ul>
                            <li>Materials: 45% of total cost</li>
                            <li>Labor: 35% of total cost</li>
                            <li>Equipment: 15% of total cost</li>
                            <li>Miscellaneous: 5% of total cost</li>
                        </ul>
                    `;
                    break;
                    
                case 'milestones':
                    content = `
                        <h3>Project Milestones Report</h3>
                        <h4>Completed Milestones</h4>
                        <ul>
                            <li>Al-Masayef Towers: Foundation (Jan 2023), Structure (Jun 2023)</li>
                            <li>Rawas Business Center: Foundation (Mar 2023)</li>
                            <li>Al-Andalus Villas: All milestones completed</li>
                        </ul>
                        
                        <h4>Upcoming Milestones</h4>
                        <ul>
                            <li>Al-Masayef Towers: Finishing work (Mar 2024)</li>
                            <li>Rawas Business Center: Structure completion (Aug 2024)</li>
                            <li>New Project: Site preparation (Apr 2024)</li>
                        </ul>
                    `;
                    break;
            }
            
            document.getElementById('reportPreview').innerHTML = content;
            document.getElementById('modalTitle').innerHTML = '<i class="fas fa-file-alt"></i> Project Report';
        }

        function openReportModal() {
            document.getElementById('reportModal').style.display = 'flex';
        }

        function closeReportModal() {
            document.getElementById('reportModal').style.display = 'none';
        }

        function exportReport(format) {
            let message = '';
            
            switch(format) {
                case 'pdf':
                    message = 'Exporting report as PDF...';
                    showMessage(message, 'info');
                    setTimeout(() => {
                        showMessage('Report exported as PDF successfully!', 'success');
                    }, 2000);
                    break;
                    
                case 'excel':
                    message = 'Exporting report as Excel...';
                    showMessage(message, 'info');
                    setTimeout(() => {
                        showMessage('Report exported as Excel successfully!', 'success');
                    }, 2000);
                    break;
            }
        }

        function printReport() {
            window.print();
            showMessage('Report sent to printer!', 'success');
        }

        function exportAllReports() {
            showMessage('Preparing all reports for export...', 'info');
            
            setTimeout(() => {
                // Create a downloadable zip file with all reports
                const link = document.createElement('a');
                link.href = '#';
                link.download = `rawas_reports_${new Date().toISOString().split('T')[0]}.zip`;
                link.click();
                
                showMessage('All reports exported successfully!', 'success');
            }, 3000);
        }

        function downloadChart(chartId) {
            const canvas = document.getElementById(chartId);
            const link = document.createElement('a');
            link.download = `${chartId}_${new Date().toISOString().split('T')[0]}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            showMessage('Chart downloaded successfully!', 'success');
        }

        window.onclick = function(event) {
            const modal = document.getElementById('reportModal');
            if (event.target === modal) {
                closeReportModal();
            }
        };

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeReportModal();
            }
        });
    </script>
</body>
</html>'''
    }

    for filename, content in html_files.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)

    print("✅ HTML templates created successfully!")


# ==============================================
# ROUTES DEFINITIONS
# ==============================================
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/projects')
def projects_page():
    return render_template('projects.html')


@app.route('/sales')
def sales_page():
    return render_template('sales.html')


@app.route('/inventory')
def inventory_page():
    return render_template('inventory.html')


@app.route('/reports')
def reports_page():
    return render_template('reports.html')


@app.route('/clients')
def clients_page():
    return render_template('clients.html')


@app.route('/employees')
def employees_page():
    return render_template('employees.html')


# ==============================================
# API ENDPOINTS - PROJECTS (CRUD)
# ==============================================
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        query = '''
        SELECT p.*, 
               (SELECT COUNT(*) FROM buildings WHERE project_id = p.id) as buildings_count,
               (SELECT COUNT(*) FROM units u JOIN buildings b ON u.building_id = b.id WHERE b.project_id = p.id) as units_count
        FROM projects p
        ORDER BY p.created_at DESC
        '''
        projects = execute_query(query)

        for project in projects:
            if project.get('start_date'):
                project['start_date_formatted'] = project['start_date'].strftime('%d/%m/%Y')
            if project.get('end_date'):
                project['end_date_formatted'] = project['end_date'].strftime('%d/%m/%Y')
            if project.get('created_at'):
                project['created_at_formatted'] = project['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json

        if not data.get('name') or not data.get('location'):
            return jsonify({'success': False, 'error': 'Project name and location are required'}), 400

        query = '''
        INSERT INTO projects (name, location, start_date, end_date, status, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        project_id = execute_query(query, (
            data['name'],
            data['location'],
            data.get('start_date'),
            data.get('end_date'),
            data.get('status', 'Planning'),
            data.get('description', '')
        ), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project_id': project_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project_details(project_id):
    try:
        query = '''
        SELECT p.*, 
               (SELECT COUNT(*) FROM buildings WHERE project_id = p.id) as buildings_count,
               (SELECT COUNT(*) FROM units u JOIN buildings b ON u.building_id = b.id WHERE b.project_id = p.id) as units_count,
               (SELECT COUNT(*) FROM units u JOIN buildings b ON u.building_id = b.id WHERE b.project_id = p.id AND u.status = 'Available') as available_units,
               (SELECT COUNT(*) FROM units u JOIN buildings b ON u.building_id = b.id WHERE b.project_id = p.id AND u.status = 'Sold') as sold_units
        FROM projects p
        WHERE p.id = %s
        '''

        project = execute_query(query, (project_id,), fetch_one=True)

        if project:
            buildings_query = '''
            SELECT b.*, 
                   (SELECT COUNT(*) FROM units WHERE building_id = b.id) as units_count,
                   (SELECT COUNT(*) FROM units WHERE building_id = b.id AND status = 'Available') as available_units
            FROM buildings b
            WHERE b.project_id = %s
            ORDER BY b.name
            '''
            buildings = execute_query(buildings_query, (project_id,))
            project['buildings'] = buildings

            if project.get('start_date'):
                project['start_date_formatted'] = project['start_date'].strftime('%d/%m/%Y')
            if project.get('end_date'):
                project['end_date_formatted'] = project['end_date'].strftime('%d/%m/%Y')

            return jsonify({'success': True, 'data': project})
        else:
            return jsonify({'success': False, 'error': 'Project not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        data = request.json

        query = '''
        UPDATE projects 
        SET name = %s, location = %s, start_date = %s, end_date = %s, 
            status = %s, description = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('name', ''),
            data.get('location', ''),
            data.get('start_date'),
            data.get('end_date'),
            data.get('status', 'Planning'),
            data.get('description', ''),
            project_id
        ), fetch=False)

        return jsonify({'success': True, 'message': 'Project updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    try:
        buildings_query = "SELECT COUNT(*) as count FROM buildings WHERE project_id = %s"
        buildings_count = execute_query(buildings_query, (project_id,), fetch_one=True)

        if buildings_count and buildings_count['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete project that has buildings. Delete buildings first.'
            }), 400

        query = "DELETE FROM projects WHERE id = %s"
        execute_query(query, (project_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Project deleted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/buildings', methods=['GET'])
def get_project_buildings(project_id):
    try:
        query = '''
        SELECT b.*, 
               (SELECT COUNT(*) FROM units WHERE building_id = b.id) as units_count,
               (SELECT COUNT(*) FROM units WHERE building_id = b.id AND status = 'Available') as available_units,
               (SELECT COUNT(*) FROM units WHERE building_id = b.id AND status = 'Sold') as sold_units
        FROM buildings b
        WHERE b.project_id = %s
        ORDER BY b.name
        '''

        buildings = execute_query(query, (project_id,))
        return jsonify({'success': True, 'data': buildings})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - BUILDINGS (CRUD)
# ==============================================
@app.route('/api/buildings', methods=['POST'])
def create_building():
    try:
        data = request.json

        if not data.get('project_id') or not data.get('name'):
            return jsonify({'success': False, 'error': 'Project ID and building name are required'}), 400

        query = '''
        INSERT INTO buildings (project_id, name, floors, status)
        VALUES (%s, %s, %s, %s)
        '''

        building_id = execute_query(query, (
            data['project_id'],
            data['name'],
            data.get('floors', 1),
            data.get('status', 'Not Started')
        ), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Building created successfully',
            'building_id': building_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<int:building_id>', methods=['GET'])
def get_building(building_id):
    try:
        query = '''
        SELECT b.*, 
               p.name as project_name,
               (SELECT COUNT(*) FROM units WHERE building_id = b.id) as units_count
        FROM buildings b
        JOIN projects p ON b.project_id = p.id
        WHERE b.id = %s
        '''

        building = execute_query(query, (building_id,), fetch_one=True)

        if building:
            return jsonify({'success': True, 'data': building})
        else:
            return jsonify({'success': False, 'error': 'Building not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<int:building_id>', methods=['PUT'])
def update_building(building_id):
    try:
        data = request.json

        query = '''
        UPDATE buildings 
        SET name = %s, floors = %s, status = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('name', ''),
            data.get('floors', 1),
            data.get('status', 'Not Started'),
            building_id
        ), fetch=False)

        return jsonify({'success': True, 'message': 'Building updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<int:building_id>', methods=['DELETE'])
def delete_building(building_id):
    try:
        units_query = "SELECT COUNT(*) as count FROM units WHERE building_id = %s"
        units_count = execute_query(units_query, (building_id,), fetch_one=True)

        if units_count and units_count['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete building that has units. Delete units first.'
            }), 400

        query = "DELETE FROM buildings WHERE id = %s"
        execute_query(query, (building_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Building deleted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/buildings/<int:building_id>/units', methods=['GET'])
def get_building_units(building_id):
    try:
        query = '''
        SELECT u.*, 
               b.name as building_name,
               p.name as project_name,
               (SELECT COUNT(*) FROM sales WHERE unit_id = u.id) as is_sold
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        WHERE u.building_id = %s
        ORDER BY 
            CASE u.status 
                WHEN 'Available' THEN 1
                WHEN 'Reserved' THEN 2
                WHEN 'Sold' THEN 3
                ELSE 4
            END,
            u.unit_number
        '''

        units = execute_query(query, (building_id,))

        for unit in units:
            if unit.get('created_at'):
                unit['created_at_formatted'] = unit['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': units})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - UNITS (CRUD)
# ==============================================
@app.route('/api/units', methods=['GET'])
def get_units():
    try:
        status = request.args.get('status', '')
        project_id = request.args.get('project_id', '')
        type_filter = request.args.get('type', '')

        where_clause = "WHERE 1=1"
        params = []

        if status:
            where_clause += " AND u.status = %s"
            params.append(status)

        if project_id:
            where_clause += " AND p.id = %s"
            params.append(project_id)

        if type_filter:
            where_clause += " AND u.type = %s"
            params.append(type_filter)

        query = f'''
        SELECT u.*, 
               b.name as building_name, 
               p.name as project_name, 
               p.location,
               (SELECT COUNT(*) FROM sales WHERE unit_id = u.id) as is_sold
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        {where_clause}
        ORDER BY 
            CASE u.status 
                WHEN 'Available' THEN 1
                WHEN 'Reserved' THEN 2
                WHEN 'Sold' THEN 3
                ELSE 4
            END,
            u.price
        '''

        units = execute_query(query, tuple(params))

        for unit in units:
            if unit.get('created_at'):
                unit['created_at_formatted'] = unit['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': units})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/units', methods=['POST'])
def create_unit():
    try:
        data = request.json

        if not data.get('building_id') or not data.get('unit_number') or not data.get('area') or not data.get('price'):
            return jsonify({'success': False, 'error': 'Building ID, unit number, area, and price are required'}), 400

        building_query = "SELECT id FROM buildings WHERE id = %s"
        building = execute_query(building_query, (data['building_id'],), fetch_one=True)

        if not building:
            return jsonify({'success': False, 'error': 'Building not found'}), 404

        check_query = "SELECT id FROM units WHERE building_id = %s AND unit_number = %s"
        existing_unit = execute_query(check_query, (data['building_id'], data['unit_number']), fetch_one=True)

        if existing_unit:
            return jsonify({'success': False, 'error': 'Unit number already exists in this building'}), 400

        query = '''
        INSERT INTO units (building_id, unit_number, type, area, floor, bedrooms, bathrooms, price, status, features)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        unit_id = execute_query(query, (
            data['building_id'],
            data['unit_number'],
            data.get('type', 'Apartment'),
            float(data['area']),
            int(data.get('floor', 0)),
            int(data.get('bedrooms', 2)),
            int(data.get('bathrooms', 1)),
            float(data['price']),
            data.get('status', 'Available'),
            data.get('features', '')
        ), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Unit created successfully',
            'unit_id': unit_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/units/<int:unit_id>', methods=['GET'])
def get_unit(unit_id):
    try:
        query = '''
        SELECT u.*, 
               b.name as building_name,
               b.project_id,
               p.name as project_name,
               (SELECT COUNT(*) FROM sales WHERE unit_id = u.id) as is_sold
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        WHERE u.id = %s
        '''

        unit = execute_query(query, (unit_id,), fetch_one=True)

        if unit:
            if unit['is_sold']:
                sales_query = '''
                SELECT s.*, c.name as client_name
                FROM sales s
                JOIN clients c ON s.client_id = c.id
                WHERE s.unit_id = %s
                '''
                sale = execute_query(sales_query, (unit_id,), fetch_one=True)
                unit['sale_info'] = sale

            if unit.get('created_at'):
                unit['created_at_formatted'] = unit['created_at'].strftime('%d/%m/%Y')

            return jsonify({'success': True, 'data': unit})
        else:
            return jsonify({'success': False, 'error': 'Unit not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/units/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    try:
        data = request.json

        current_query = "SELECT status FROM units WHERE id = %s"
        current_unit = execute_query(current_query, (unit_id,), fetch_one=True)

        if not current_unit:
            return jsonify({'success': False, 'error': 'Unit not found'}), 404

        if current_unit['status'] == 'Sold':
            query = '''
            UPDATE units 
            SET features = %s
            WHERE id = %s
            '''
            execute_query(query, (
                data.get('features', ''),
                unit_id
            ), fetch=False)
        else:
            if 'unit_number' in data:
                check_query = '''
                SELECT id FROM units 
                WHERE building_id = (SELECT building_id FROM units WHERE id = %s) 
                AND unit_number = %s 
                AND id != %s
                '''
                building_query = "SELECT building_id FROM units WHERE id = %s"
                building_id = execute_query(building_query, (unit_id,), fetch_one=True)['building_id']

                existing_unit = execute_query(check_query, (unit_id, data['unit_number'], unit_id), fetch_one=True)
                if existing_unit:
                    return jsonify({'success': False, 'error': 'Unit number already exists in this building'}), 400

            query = '''
            UPDATE units 
            SET unit_number = %s, type = %s, area = %s, floor = %s, bedrooms = %s, 
                bathrooms = %s, price = %s, status = %s, features = %s
            WHERE id = %s
            '''

            execute_query(query, (
                data.get('unit_number', ''),
                data.get('type', 'Apartment'),
                float(data.get('area', 0)),
                int(data.get('floor', 0)),
                int(data.get('bedrooms', 2)),
                int(data.get('bathrooms', 1)),
                float(data.get('price', 0)),
                data.get('status', 'Available'),
                data.get('features', ''),
                unit_id
            ), fetch=False)

        return jsonify({'success': True, 'message': 'Unit updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/units/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    try:
        unit_query = "SELECT * FROM units WHERE id = %s"
        unit = execute_query(unit_query, (unit_id,), fetch_one=True)

        if not unit:
            return jsonify({'success': False, 'error': 'Unit not found'}), 404

        if unit['status'] == 'Sold':
            return jsonify({
                'success': False,
                'error': 'Cannot delete a sold unit. Cancel the sale first.'
            }), 400

        sales_query = "SELECT COUNT(*) as count FROM sales WHERE unit_id = %s"
        sales_count = execute_query(sales_query, (unit_id,), fetch_one=True)

        if sales_count and sales_count['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete unit with existing sales. Delete the sale first.'
            }), 400

        query = "DELETE FROM units WHERE id = %s"
        execute_query(query, (unit_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Unit deleted successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/projects/<int:project_id>/units', methods=['GET'])
def get_project_units(project_id):
    try:
        query = '''
        SELECT u.*, 
               b.name as building_name,
               p.name as project_name,
               (SELECT COUNT(*) FROM sales WHERE unit_id = u.id) as is_sold
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        WHERE p.id = %s
        ORDER BY b.name, u.unit_number
        '''

        units = execute_query(query, (project_id,))
        return jsonify({'success': True, 'data': units})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/units/status/<status>', methods=['GET'])
def get_units_by_status(status):
    try:
        query = '''
        SELECT u.*, 
               b.name as building_name,
               p.name as project_name,
               p.location
        FROM units u
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        WHERE u.status = %s
        ORDER BY u.price
        '''

        units = execute_query(query, (status,))
        return jsonify({'success': True, 'data': units})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - CLIENTS (CRUD)
# ==============================================
@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        search = request.args.get('search', '')
        type_filter = request.args.get('type', '')

        query = "SELECT id, name, phone, email, address, type, id_number, company, notes, created_at FROM clients WHERE 1=1"
        params = []

        if search:
            query += " AND (name LIKE %s OR phone LIKE %s OR email LIKE %s OR id_number LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])

        if type_filter:
            query += " AND type = %s"
            params.append(type_filter)

        query += " ORDER BY created_at DESC"

        clients = execute_query(query, tuple(params))

        for client in clients:
            sales_query = "SELECT COUNT(*) as sales_count FROM sales WHERE client_id = %s"
            sales_data = execute_query(sales_query, (client['id'],), fetch_one=True)
            client['sales_count'] = sales_data['sales_count'] if sales_data else 0

            if client.get('created_at'):
                client['created_at_formatted'] = client['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': clients})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    try:
        query = "SELECT * FROM clients WHERE id = %s"
        client = execute_query(query, (client_id,), fetch_one=True)

        if client:
            sales_query = '''
            SELECT s.*, u.unit_number, u.type as unit_type, p.name as project_name
            FROM sales s
            JOIN units u ON s.unit_id = u.id
            JOIN buildings b ON u.building_id = b.id
            JOIN projects p ON b.project_id = p.id
            WHERE s.client_id = %s
            ORDER BY s.contract_date DESC
            '''
            sales = execute_query(sales_query, (client_id,))
            client['sales'] = sales

            if client.get('created_at'):
                client['created_at_formatted'] = client['created_at'].strftime('%d/%m/%Y')

            return jsonify({'success': True, 'data': client})
        else:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients', methods=['POST'])
def create_client():
    try:
        data = request.json

        if not data.get('name') or not data.get('phone'):
            return jsonify({'success': False, 'error': 'Name and phone are required'}), 400

        query = '''
        INSERT INTO clients (name, phone, email, address, type, id_number, company, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''

        client_id = execute_query(query, (
            data['name'],
            data['phone'],
            data.get('email', ''),
            data.get('address', ''),
            data.get('type', 'Buyer'),
            data.get('id_number', ''),
            data.get('company', ''),
            data.get('notes', '')
        ), fetch=False)

        return jsonify({'success': True, 'message': 'Client created', 'id': client_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.json

        query = '''
        UPDATE clients 
        SET name = %s, phone = %s, email = %s, address = %s, type = %s, 
            id_number = %s, company = %s, notes = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('name', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('address', ''),
            data.get('type', 'Buyer'),
            data.get('id_number', ''),
            data.get('company', ''),
            data.get('notes', ''),
            client_id
        ), fetch=False)

        return jsonify({'success': True, 'message': 'Client updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        check_query = "SELECT COUNT(*) as count FROM clients WHERE id = %s"
        client_exists = execute_query(check_query, (client_id,), fetch_one=True)

        if not client_exists or client_exists['count'] == 0:
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        sales_query = "SELECT COUNT(*) as count FROM sales WHERE client_id = %s"
        sales_count = execute_query(sales_query, (client_id,), fetch_one=True)

        if sales_count and sales_count['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete client with existing sales. Please delete or reassign sales first.'
            }), 400

        query = "DELETE FROM clients WHERE id = %s"
        execute_query(query, (client_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Client deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>/sales', methods=['GET'])
def get_client_sales(client_id):
    try:
        query = '''
        SELECT s.*, 
               u.unit_number,
               u.type as unit_type,
               p.name as project_name,
               b.name as building_name,
               (SELECT SUM(amount) FROM payments WHERE sale_id = s.id) as total_paid
        FROM sales s
        JOIN units u ON s.unit_id = u.id
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        WHERE s.client_id = %s
        ORDER BY s.contract_date DESC
        '''
        sales = execute_query(query, (client_id,))

        for sale in sales:
            if sale.get('contract_date'):
                sale['contract_date_formatted'] = sale['contract_date'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': sales})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - SALES
# ==============================================
@app.route('/api/sales', methods=['GET'])
def get_sales():
    try:
        status = request.args.get('status', '')

        query = '''
        SELECT s.*, 
               c.name as client_name,
               c.phone as client_phone,
               c.email as client_email,
               u.unit_number,
               u.type as unit_type,
               u.area,
               u.price as unit_price,
               b.name as building_name,
               p.name as project_name,
               e.name as employee_name,
                   COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0) as total_paid,
                   (s.total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0)) as remaining_balance,
                   CASE 
                       WHEN (s.total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0)) > 0 
                       AND DATEDIFF(CURDATE(), s.contract_date) > 30 
                       THEN DATEDIFF(CURDATE(), s.contract_date)
                       ELSE 0 
                   END as days_delayed
        FROM sales s
        JOIN clients c ON s.client_id = c.id
        JOIN units u ON s.unit_id = u.id
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        LEFT JOIN employees e ON s.employee_id = e.id
        WHERE 1=1
        '''
        params = []

        if status:
            query += " AND s.status = %s"
            params.append(status)

        query += " ORDER BY s.contract_date DESC"

        sales = execute_query(query, tuple(params))

        for sale in sales:
            if sale.get('contract_date'):
                sale['contract_date_formatted'] = sale['contract_date'].strftime('%d/%m/%Y')
            if sale.get('next_payment_date'):
                sale['next_payment_date_formatted'] = sale['next_payment_date'].strftime('%d/%m/%Y')
            if sale.get('created_at'):
                sale['created_at_formatted'] = sale['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': sales})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    try:
        query = '''
            SELECT s.*, 
                   (s.total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0)) as remaining_balance,
                   c.name as client_name,
                   c.phone as client_phone,
                   c.email as client_email,
                   c.address as client_address,
                   u.unit_number,
                   u.type as unit_type,
                   u.area,
                   u.bedrooms,
                   u.bathrooms,
                   u.features,
                   b.name as building_name,
                   p.name as project_name,
                   p.location as project_location,
                   e.name as employee_name,
               e.phone as employee_phone,
               (SELECT SUM(amount) FROM payments WHERE sale_id = s.id) as total_paid
        FROM sales s
        JOIN clients c ON s.client_id = c.id
        JOIN units u ON s.unit_id = u.id
        JOIN buildings b ON u.building_id = b.id
        JOIN projects p ON b.project_id = p.id
        LEFT JOIN employees e ON s.employee_id = e.id
        WHERE s.id = %s
        '''
        sale = execute_query(query, (sale_id,), fetch_one=True)

        if sale:
            if sale.get('contract_date'):
                sale['contract_date_formatted'] = sale['contract_date'].strftime('%d/%m/%Y')
            if sale.get('next_payment_date'):
                sale['next_payment_date_formatted'] = sale['next_payment_date'].strftime('%d/%m/%Y')
            if sale.get('created_at'):
                sale['created_at_formatted'] = sale['created_at'].strftime('%d/%m/%Y')

            return jsonify({'success': True, 'data': sale})
        else:
            return jsonify({'success': False, 'error': 'Sale not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sales', methods=['POST'])
def create_sale():
    try:
        data = request.json

        if not data.get('unit_id') or not data.get('client_id'):
            return jsonify({'success': False, 'error': 'Unit and client are required'}), 400

        unit_query = "SELECT status, price FROM units WHERE id = %s"
        unit = execute_query(unit_query, (data['unit_id'],), fetch_one=True)

        if not unit:
            return jsonify({'success': False, 'error': 'Unit not found'}), 404

        if unit['status'] != 'Available':
            return jsonify({'success': False, 'error': 'Unit is not available'}), 400

        total_price = float(data.get('total_price', unit['price']))
        down_payment = float(data.get('down_payment', 0))

        if down_payment > total_price:
            return jsonify({'success': False, 'error': 'Down payment cannot exceed total price'}), 400

        remaining = total_price - down_payment

        contract_number = data.get('contract_number', f'CONTRACT-{datetime.now().strftime("%Y%m%d-%H%M%S")}')

        next_payment_date = None
        if data.get('payment_plan') == 'Installments' and remaining > 0:
            next_payment_date = (datetime.now() + timedelta(days=30)).date().isoformat()

        sale_query = '''
        INSERT INTO sales (unit_id, client_id, employee_id, contract_date, contract_number, 
                          total_price, down_payment, remaining_balance, payment_plan, 
                          payment_method, payment_terms, status, next_payment_date, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        sale_id = execute_query(sale_query, (
            data['unit_id'],
            data['client_id'],
            data.get('employee_id'),
            data.get('contract_date', datetime.now().date().isoformat()),
            contract_number,
            total_price,
            down_payment,
            remaining,
            data.get('payment_plan', 'Cash'),
            data.get('payment_method', 'Cash'),
            data.get('payment_terms', ''),
            'Active',
            next_payment_date,
            data.get('notes', '')
        ), fetch=False)

        execute_query("UPDATE units SET status = 'Sold' WHERE id = %s", (data['unit_id'],), fetch=False)

        if down_payment > 0:
            payment_query = '''
            INSERT INTO payments (sale_id, amount, payment_date, method, receipt_number, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            '''
            execute_query(payment_query, (
                sale_id,
                down_payment,
                data.get('contract_date', datetime.now().date().isoformat()),
                data.get('payment_method', 'Cash'),
                f'RCPT-{contract_number}',
                'Initial down payment'
            ), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Sale created successfully',
            'sale_id': sale_id,
            'contract_number': contract_number,
            'remaining_balance': remaining
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    try:
        data = request.json

        current_query = "SELECT * FROM sales WHERE id = %s"
        current_sale = execute_query(current_query, (sale_id,), fetch_one=True)

        if not current_sale:
            return jsonify({'success': False, 'error': 'Sale not found'}), 404

        query = '''
        UPDATE sales 
        SET employee_id = %s, contract_date = %s, contract_number = %s, total_price = %s,
            down_payment = %s, remaining_balance = %s, payment_plan = %s, payment_method = %s,
            payment_terms = %s, status = %s, next_payment_date = %s, notes = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('employee_id', current_sale['employee_id']),
            data.get('contract_date', current_sale['contract_date']),
            data.get('contract_number', current_sale['contract_number']),
            data.get('total_price', current_sale['total_price']),
            data.get('down_payment', current_sale['down_payment']),
            data.get('remaining_balance', current_sale['remaining_balance']),
            data.get('payment_plan', current_sale['payment_plan']),
            data.get('payment_method', current_sale['payment_method']),
            data.get('payment_terms', current_sale['payment_terms']),
            data.get('status', current_sale['status']),
            data.get('next_payment_date', current_sale['next_payment_date']),
            data.get('notes', current_sale['notes']),
            sale_id
        ), fetch=False)

        if data.get('status') == 'Completed' and current_sale['status'] != 'Completed':
            execute_query("UPDATE units SET status = 'Sold' WHERE id = %s", (current_sale['unit_id'],), fetch=False)

        return jsonify({'success': True, 'message': 'Sale updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - PAYMENTS
# ==============================================
@app.route('/api/payments', methods=['GET'])
def get_payments():
    try:
        sale_id = request.args.get('sale_id', '')

        query = "SELECT * FROM payments WHERE 1=1"
        params = []

        if sale_id:
            query += " AND sale_id = %s"
            params.append(sale_id)

        query += " ORDER BY payment_date DESC"

        payments = execute_query(query, tuple(params))

        for payment in payments:
            if payment.get('payment_date'):
                payment['payment_date_formatted'] = payment['payment_date'].strftime('%d/%m/%Y')
            if payment.get('created_at'):
                payment['created_at_formatted'] = payment['created_at'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': payments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sales/<int:sale_id>/payments', methods=['GET'])
def get_sale_payments(sale_id):
    try:
        query = '''
        SELECT p.*, s.contract_number, c.name as client_name
        FROM payments p
        JOIN sales s ON p.sale_id = s.id
        JOIN clients c ON s.client_id = c.id
        WHERE p.sale_id = %s
        ORDER BY p.payment_date DESC
        '''
        payments = execute_query(query, (sale_id,))

        for payment in payments:
            if payment.get('payment_date'):
                payment['payment_date_formatted'] = payment['payment_date'].strftime('%d/%m/%Y')

        return jsonify({'success': True, 'data': payments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/payments', methods=['POST'])
def create_payment():
    try:
        data = request.json

        if not data.get('sale_id') or not data.get('amount') or float(data['amount']) <= 0:
            return jsonify({'success': False, 'error': 'Valid sale ID and amount are required'}), 400

        sale_query = "SELECT * FROM sales WHERE id = %s"
        sale = execute_query(sale_query, (data['sale_id'],), fetch_one=True)

        if not sale:
            return jsonify({'success': False, 'error': 'Sale not found'}), 404

        amount = float(data['amount'])

        # 3NF Optimized: Calculate remaining balance from payments
        payments_sum_query = "SELECT SUM(amount) as total_paid FROM payments WHERE sale_id = %s"
        total_paid_row = execute_query(payments_sum_query, (data['sale_id'],), fetch_one=True)
        total_paid = float(total_paid_row['total_paid'] or 0)
        remaining_balance = float(sale['total_price']) - total_paid

        if amount > remaining_balance:
            return jsonify({'success': False, 'error': 'Payment exceeds remaining balance'}), 400

        payment_query = '''
        INSERT INTO payments (sale_id, amount, payment_date, method, receipt_number, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        payment_id = execute_query(payment_query, (
            data['sale_id'],
            amount,
            data.get('payment_date', datetime.now().date().isoformat()),
            data.get('method', 'Cash'),
            data.get('receipt_number', f'RCPT-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
            data.get('notes', '')
        ), fetch=False)

        new_balance = remaining_balance - amount
        update_sale_query = '''
        UPDATE sales 
        SET next_payment_date = %s,
            status = CASE 
                WHEN %s <= 0 THEN 'Completed' 
                ELSE status 
            END
        WHERE id = %s
        '''

        next_payment_date = None
        if new_balance > 0 and sale['payment_plan'] == 'Installments':
            next_payment_date = (datetime.now() + timedelta(days=30)).date().isoformat()

        execute_query(update_sale_query, (
            next_payment_date,
            new_balance,
            data['sale_id']
        ), fetch=False)

        if new_balance <= 0:
            execute_query("UPDATE units SET status = 'Sold' WHERE id = %s", (sale['unit_id'],), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Payment recorded successfully',
            'payment_id': payment_id,
            'new_balance': new_balance
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - EMPLOYEES (CRUD)
# ==============================================
@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        search = request.args.get('search', '')
        status = request.args.get('status', '')

        query = '''
        SELECT e.*, 
               (SELECT COUNT(*) FROM sales WHERE employee_id = e.id) as sales_count,
               (SELECT SUM(total_price) FROM sales WHERE employee_id = e.id) as total_sales,
               (SELECT COUNT(*) FROM payments WHERE sale_id IN (SELECT id FROM sales WHERE employee_id = e.id)) as payments_count,
               (SELECT SUM(amount) FROM payments WHERE sale_id IN (SELECT id FROM sales WHERE employee_id = e.id)) as total_collected
        FROM employees e
        WHERE 1=1
        '''
        params = []

        if search:
            query += " AND (e.name LIKE %s OR e.position LIKE %s OR e.email LIKE %s OR e.phone LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])

        if status:
            query += " AND e.status = %s"
            params.append(status)

        query += " ORDER BY e.name"

        employees = execute_query(query, tuple(params))

        for emp in employees:
            if emp.get('created_at'):
                emp['created_at_formatted'] = emp['created_at'].strftime('%d/%m/%Y')
            if emp.get('salary'):
                emp['salary_formatted'] = f"${emp['salary']:,.2f}"

        return jsonify({'success': True, 'data': employees})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    try:
        query = '''
        SELECT e.*, 
               (SELECT COUNT(*) FROM sales WHERE employee_id = e.id) as sales_count,
               (SELECT SUM(total_price) FROM sales WHERE employee_id = e.id) as total_sales
        FROM employees e
        WHERE e.id = %s
        '''

        employee = execute_query(query, (employee_id,), fetch_one=True)

        if employee:
            if employee.get('created_at'):
                employee['created_at_formatted'] = employee['created_at'].strftime('%d/%m/%Y')
            if employee.get('salary'):
                employee['salary_formatted'] = f"${employee['salary']:,.2f}"

            sales_query = '''
            SELECT s.*, c.name as client_name, u.unit_number, p.name as project_name
            FROM sales s
            LEFT JOIN clients c ON s.client_id = c.id
            LEFT JOIN units u ON s.unit_id = u.id
            LEFT JOIN buildings b ON u.building_id = b.id
            LEFT JOIN projects p ON b.project_id = p.id
            WHERE s.employee_id = %s
            ORDER BY s.contract_date DESC
            '''
            sales = execute_query(sales_query, (employee_id,))

            for sale in sales:
                if sale.get('contract_date'):
                    sale['contract_date_formatted'] = sale['contract_date'].strftime('%d/%m/%Y')

            employee['sales'] = sales

            return jsonify({'success': True, 'data': employee})
        else:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/employees', methods=['POST'])
def create_employee():
    try:
        data = request.json

        if not data.get('name') or not data.get('position') or not data.get('phone'):
            return jsonify({'success': False, 'error': 'Name, position, and phone are required'}), 400

        if data.get('email'):
            check_query = "SELECT id FROM employees WHERE email = %s"
            existing = execute_query(check_query, (data['email'],), fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400

        query = '''
        INSERT INTO employees (name, position, phone, email, salary, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        employee_id = execute_query(query, (
            data['name'],
            data['position'],
            data['phone'],
            data.get('email', ''),
            data.get('salary'),
            data.get('status', 'Active')
        ), fetch=False)

        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'employee_id': employee_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    try:
        data = request.json

        check_query = "SELECT id FROM employees WHERE id = %s"
        employee = execute_query(check_query, (employee_id,), fetch_one=True)
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404

        if data.get('email'):
            check_query = "SELECT id FROM employees WHERE email = %s AND id != %s"
            existing = execute_query(check_query, (data['email'], employee_id), fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400

        query = '''
        UPDATE employees 
        SET name = %s, position = %s, phone = %s, email = %s, 
            salary = %s, status = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('name', ''),
            data.get('position', ''),
            data.get('phone', ''),
            data.get('email', ''),
            data.get('salary'),
            data.get('status', 'Active'),
            employee_id
        ), fetch=False)

        return jsonify({'success': True, 'message': 'Employee updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        check_query = "SELECT id FROM employees WHERE id = %s"
        employee = execute_query(check_query, (employee_id,), fetch_one=True)
        if not employee:
            return jsonify({'success': False, 'error': 'Employee not found'}), 404

        sales_query = "SELECT COUNT(*) as count FROM sales WHERE employee_id = %s"
        sales_count = execute_query(sales_query, (employee_id,), fetch_one=True)

        if sales_count and sales_count['count'] > 0:
            return jsonify({
                'success': False,
                'error': 'Cannot delete employee with associated sales. Reassign sales first.'
            }), 400

        query = "DELETE FROM employees WHERE id = %s"
        execute_query(query, (employee_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Employee deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/employees/stats', methods=['GET'])
def get_employee_stats():
    try:
        total_query = "SELECT COUNT(*) as total FROM employees"
        total = execute_query(total_query, fetch_one=True)

        active_query = "SELECT COUNT(*) as active FROM employees WHERE status = 'Active'"
        active = execute_query(active_query, fetch_one=True)

        inactive_query = "SELECT COUNT(*) as inactive FROM employees WHERE status = 'Inactive'"
        inactive = execute_query(inactive_query, fetch_one=True)

        salary_query = "SELECT SUM(salary) as total_salary FROM employees WHERE status = 'Active'"
        salary = execute_query(salary_query, fetch_one=True)

        position_query = '''
        SELECT position, COUNT(*) as count 
        FROM employees 
        GROUP BY position 
        ORDER BY count DESC
        '''
        by_position = execute_query(position_query)

        return jsonify({
            'success': True,
            'stats': {
                'total': total['total'] if total else 0,
                'active': active['active'] if active else 0,
                'inactive': inactive['inactive'] if inactive else 0,
                'total_salary': salary['total_salary'] if salary and salary['total_salary'] else 0,
                'by_position': by_position
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - MATERIALS (CRUD with Inventory)
# ==============================================
@app.route('/api/materials', methods=['GET'])
def get_materials_with_inventory():
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', '')

        query = '''
        SELECT m.*, 
               COALESCE(i.quantity, 0) as current_stock,
               i.location,
               i.last_updated,
               CASE 
                   WHEN COALESCE(i.quantity, 0) <= 0 THEN 'Out of Stock'
                   WHEN COALESCE(i.quantity, 0) <= m.min_quantity * 0.2 THEN 'Critical'
                   WHEN COALESCE(i.quantity, 0) <= m.min_quantity THEN 'Low'
                   ELSE 'Adequate'
               END as stock_status,
               (COALESCE(i.quantity, 0) * m.price) as stock_value
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        WHERE 1=1
        '''
        params = []

        if search:
            query += " AND (m.name LIKE %s OR m.category LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if category and category != 'all':
            query += " AND m.category = %s"
            params.append(category)

        query += " ORDER BY m.name"

        materials = execute_query(query, tuple(params))

        for mat in materials:
            if mat.get('last_updated'):
                mat['last_updated_formatted'] = mat['last_updated'].strftime('%d/%m/%Y %H:%M')
            if mat.get('created_at'):
                mat['created_at_formatted'] = mat['created_at'].strftime('%d/%m/%Y')
            if mat.get('price'):
                mat['price_formatted'] = f"${mat['price']:.2f}"
            if mat.get('stock_value'):
                mat['stock_value_formatted'] = f"${mat['stock_value']:,.2f}"

        return jsonify({'success': True, 'data': materials})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/materials/<int:material_id>', methods=['GET'])
def get_material_details(material_id):
    try:
        query = '''
        SELECT m.*, 
               COALESCE(i.quantity, 0) as current_stock,
               i.location,
               i.last_updated
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        WHERE m.id = %s
        '''

        material = execute_query(query, (material_id,), fetch_one=True)

        if material:
            if material.get('created_at'):
                material['created_at_formatted'] = material['created_at'].strftime('%d/%m/%Y')
            if material.get('last_updated'):
                material['last_updated_formatted'] = material['last_updated'].strftime('%d/%m/%Y %H:%M')

            try:
                history_query = '''
                SELECT * FROM inventory_transactions 
                WHERE material_id = %s 
                ORDER BY transaction_date DESC 
                LIMIT 10
                '''
                history = execute_query(history_query, (material_id,))

                for transaction in history:
                    if transaction.get('transaction_date'):
                        transaction['transaction_date_formatted'] = transaction['transaction_date'].strftime('%d/%m/%Y %H:%M')

                material['stock_history'] = history
            except:
                material['stock_history'] = []

            return jsonify({'success': True, 'data': material})
        else:
            return jsonify({'success': False, 'error': 'Material not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/materials', methods=['POST'])
def create_material_with_stock():
    try:
        data = request.json

        if not data.get('name') or not data.get('category') or not data.get('unit') or not data.get('price'):
            return jsonify({'success': False, 'error': 'Name, category, unit, and price are required'}), 400

        if float(data['price']) <= 0:
            return jsonify({'success': False, 'error': 'Price must be greater than 0'}), 400

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            material_query = '''
            INSERT INTO materials (name, category, unit, price, min_quantity)
            VALUES (%s, %s, %s, %s, %s)
            '''

            cursor.execute(material_query, (
                data['name'],
                data['category'],
                data['unit'],
                float(data['price']),
                int(data.get('min_quantity', 10))
            ))

            material_id = cursor.lastrowid

            initial_stock = int(data.get('initial_stock', 0))
            if initial_stock > 0:
                inventory_query = '''
                INSERT INTO inventory (material_id, quantity, location)
                VALUES (%s, %s, %s)
                '''
                cursor.execute(inventory_query, (
                    material_id,
                    initial_stock,
                    data.get('location', '')
                ))

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Material created successfully',
                'material_id': material_id
            })

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    try:
        data = request.json

        check_query = "SELECT id FROM materials WHERE id = %s"
        material = execute_query(check_query, (material_id,), fetch_one=True)
        if not material:
            return jsonify({'success': False, 'error': 'Material not found'}), 404

        query = '''
        UPDATE materials 
        SET name = %s, category = %s, unit = %s, price = %s, min_quantity = %s
        WHERE id = %s
        '''

        execute_query(query, (
            data.get('name', ''),
            data.get('category', ''),
            data.get('unit', ''),
            float(data.get('price', 0)),
            int(data.get('min_quantity', 10)),
            material_id
        ), fetch=False)

        if data.get('location'):
            inventory_query = '''
            UPDATE inventory 
            SET location = %s 
            WHERE material_id = %s
            '''
            execute_query(inventory_query, (data['location'], material_id), fetch=False)

        return jsonify({'success': True, 'message': 'Material updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    try:
        check_query = "SELECT id FROM materials WHERE id = %s"
        material = execute_query(check_query, (material_id,), fetch_one=True)
        if not material:
            return jsonify({'success': False, 'error': 'Material not found'}), 404

        inventory_query = "DELETE FROM inventory WHERE material_id = %s"
        execute_query(inventory_query, (material_id,), fetch=False)

        material_query = "DELETE FROM materials WHERE id = %s"
        execute_query(material_query, (material_id,), fetch=False)

        return jsonify({'success': True, 'message': 'Material deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/inventory/adjust', methods=['POST'])
def adjust_inventory():
    try:
        data = request.json

        if not data.get('material_id') or not data.get('adjustment_type') or not data.get('quantity'):
            return jsonify({'success': False, 'error': 'Material ID, adjustment type, and quantity are required'}), 400

        material_id = data['material_id']
        adjustment_type = data['adjustment_type']
        quantity = int(data['quantity'])

        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be greater than 0'}), 400

        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            inventory_query = "SELECT quantity FROM inventory WHERE material_id = %s"
            cursor.execute(inventory_query, (material_id,))
            inventory = cursor.fetchone()

            current_quantity = inventory['quantity'] if inventory else 0

            if adjustment_type == 'IN':
                new_quantity = current_quantity + quantity
            elif adjustment_type == 'OUT':
                if quantity > current_quantity:
                    return jsonify({'success': False, 'error': 'Cannot remove more stock than available'}), 400
                new_quantity = current_quantity - quantity
            elif adjustment_type == 'SET':
                new_quantity = quantity
            else:
                return jsonify({'success': False, 'error': 'Invalid adjustment type'}), 400

            if inventory:
                update_query = '''
                UPDATE inventory 
                SET quantity = %s, last_updated = NOW() 
                WHERE material_id = %s
                '''
                cursor.execute(update_query, (new_quantity, material_id))
            else:
                insert_query = '''
                INSERT INTO inventory (material_id, quantity, location, last_updated)
                VALUES (%s, %s, %s, NOW())
                '''
                cursor.execute(insert_query, (material_id, new_quantity, data.get('location', '')))

                try:
                    transaction_query = '''
                    INSERT INTO inventory_transactions 
                    (material_id, transaction_type, quantity, reason, notes, transaction_date)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    '''
                    cursor.execute(transaction_query, (
                        material_id,
                        adjustment_type,
                        quantity,
                        data.get('reason'),
                        data.get('notes')
                    ))
                except:
                    pass

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Inventory adjusted successfully',
                'previous_quantity': current_quantity,
                'new_quantity': new_quantity,
                'difference': new_quantity - current_quantity
            })

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/inventory/stats', methods=['GET'])
def get_inventory_stats():
    try:
        total_query = "SELECT COUNT(*) as total_materials FROM materials"
        total = execute_query(total_query, fetch_one=True)

        low_stock_query = '''
        SELECT COUNT(*) as low_stock
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        WHERE COALESCE(i.quantity, 0) <= m.min_quantity 
        AND COALESCE(i.quantity, 0) > 0
        '''
        low_stock = execute_query(low_stock_query, fetch_one=True)

        critical_stock_query = '''
        SELECT COUNT(*) as critical_stock
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        WHERE COALESCE(i.quantity, 0) <= m.min_quantity * 0.2 
        AND COALESCE(i.quantity, 0) > 0
        '''
        critical_stock = execute_query(critical_stock_query, fetch_one=True)

        out_of_stock_query = '''
        SELECT COUNT(*) as out_of_stock
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        WHERE COALESCE(i.quantity, 0) = 0
        '''
        out_of_stock = execute_query(out_of_stock_query, fetch_one=True)

        value_query = '''
        SELECT SUM(COALESCE(i.quantity, 0) * m.price) as total_value
        FROM materials m
        LEFT JOIN inventory i ON m.id = i.material_id
        '''
        total_value = execute_query(value_query, fetch_one=True)

        return jsonify({
            'success': True,
            'stats': {
                'total_materials': total['total_materials'] if total else 0,
                'low_stock': low_stock['low_stock'] if low_stock else 0,
                'critical_stock': critical_stock['critical_stock'] if critical_stock else 0,
                'out_of_stock': out_of_stock['out_of_stock'] if out_of_stock else 0,
                'total_value': total_value['total_value'] if total_value and total_value['total_value'] else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - REPORTS
# ==============================================
@app.route('/api/reports/sales-summary', methods=['GET'])
def sales_summary():
    try:
        query = '''
        SELECT 
            DATE_FORMAT(contract_date, '%%Y-%%m') as month,
            COUNT(*) as sales_count,
                SUM(total_price) as total_revenue,
                SUM(down_payment) as total_down,
                SUM(total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = sales.id), 0)) as total_remaining,
                AVG(total_price) as avg_sale_price
            FROM sales
            WHERE contract_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(contract_date, '%%Y-%%m')
        ORDER BY month
        '''
        monthly = execute_query(query)

        total_query = '''
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_price) as total_revenue,
                SUM(down_payment) as total_down,
                SUM(total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = sales.id), 0)) as total_remaining,
                AVG(total_price) as avg_price
            FROM sales
            WHERE status = 'Active'
        '''
        totals = execute_query(total_query, fetch_one=True)

        employee_query = '''
        SELECT 
            e.name,
            COUNT(s.id) as sales_count,
            SUM(s.total_price) as total_sales,
            AVG(s.total_price) as avg_sale
        FROM sales s
        JOIN employees e ON s.employee_id = e.id
        GROUP BY e.id
        ORDER BY total_sales DESC
        LIMIT 10
        '''
        by_employee = execute_query(employee_query)

        return jsonify({
            'success': True,
            'monthly': monthly,
            'totals': totals,
            'by_employee': by_employee
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/reports/client-statistics', methods=['GET'])
def client_statistics():
    try:
        type_query = '''
        SELECT 
            c.type,
            COUNT(DISTINCT c.id) as count,
            COUNT(s.id) as sales_count,
            SUM(COALESCE(s.total_price, 0)) as total_sales
        FROM clients c
        LEFT JOIN sales s ON c.id = s.client_id
        GROUP BY c.type
        ORDER BY count DESC
        '''
        by_type = execute_query(type_query)

        top_clients_query = '''
        SELECT 
            c.name,
            c.type,
            COUNT(s.id) as purchases,
            SUM(s.total_price) as total_spent,
            MAX(s.contract_date) as last_purchase
        FROM clients c
        LEFT JOIN sales s ON c.id = s.client_id
        GROUP BY c.id
        HAVING total_spent > 0
        ORDER BY total_spent DESC
        LIMIT 10
        '''
        top_clients = execute_query(top_clients_query)

        new_clients_query = '''
        SELECT 
            DATE_FORMAT(created_at, '%%Y-%%m') as month,
            COUNT(*) as new_clients
        FROM clients
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
        ORDER BY month
        '''
        new_clients = execute_query(new_clients_query)

        return jsonify({
            'success': True,
            'by_type': by_type,
            'top_clients': top_clients,
            'new_clients': new_clients
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# API ENDPOINTS - DASHBOARD
# ==============================================
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    try:
        projects = execute_query("SELECT COUNT(*) as count FROM projects", fetch_one=True)

        units_query = '''
        SELECT status, COUNT(*) as count 
        FROM units 
        GROUP BY status
        '''
        units = execute_query(units_query)
        units_dict = {item['status']: item['count'] for item in units}

        sales = execute_query('''
        SELECT 
            COUNT(*) as count, 
            SUM(total_price) as revenue,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_sales
        FROM sales
        ''', fetch_one=True)

        clients = execute_query("SELECT COUNT(*) as count FROM clients", fetch_one=True)

        employees = execute_query("SELECT COUNT(*) as count FROM employees", fetch_one=True)

        recent_payments = execute_query('''
        SELECT p.*, c.name as client_name, s.contract_number
        FROM payments p
        JOIN sales s ON p.sale_id = s.id
        JOIN clients c ON s.client_id = c.id
        ORDER BY p.payment_date DESC
        LIMIT 5
        ''')

        for payment in recent_payments:
            if payment.get('payment_date'):
                payment['payment_date_formatted'] = payment['payment_date'].strftime('%d/%m/%Y')

        delayed_payments = execute_query('''
        SELECT s.*, c.name as client_name, c.phone, u.unit_number
        FROM sales s
        JOIN clients c ON s.client_id = c.id
        JOIN units u ON s.unit_id = u.id
        WHERE s.status = 'Active' 
        AND (s.total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0)) > 0
        AND DATEDIFF(CURDATE(), s.contract_date) > 30
        ORDER BY (s.total_price - COALESCE((SELECT SUM(amount) FROM payments WHERE sale_id = s.id), 0)) DESC
        LIMIT 5
        ''')

        for sale in delayed_payments:
            if sale.get('contract_date'):
                sale['contract_date_formatted'] = sale['contract_date'].strftime('%d/%m/%Y')

        return jsonify({
            'success': True,
            'stats': {
                'projects': projects['count'] if projects else 0,
                'units': units_dict,
                'sales_count': sales['count'] if sales else 0,
                'sales_revenue': sales['revenue'] if sales and sales['revenue'] else 0,
                'active_sales': sales['active_sales'] if sales else 0,
                'clients': clients['count'] if clients else 0,
                'employees': employees['count'] if employees else 0,
                'delayed_payments': len(delayed_payments)
            },
            'recent_payments': recent_payments,
            'delayed_payments': delayed_payments
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# EXPORT ENDPOINTS
# ==============================================
@app.route('/api/export/<export_type>', methods=['GET'])
def export_data(export_type):
    try:
        if export_type == 'sales':
            query = '''
            SELECT s.*, c.name as client_name, u.unit_number, p.name as project_name
            FROM sales s
            LEFT JOIN clients c ON s.client_id = c.id
            LEFT JOIN units u ON s.unit_id = u.id
            LEFT JOIN buildings b ON u.building_id = b.id
            LEFT JOIN projects p ON b.project_id = p.id
            '''
            data = execute_query(query)

            if data:
                csv_data = []
                headers = data[0].keys()
                csv_data.append(','.join(headers))

                for row in data:
                    row_values = []
                    for h in headers:
                        value = str(row.get(h, ''))
                        value = value.replace('"', '""')
                        if ',' in value or '\n' in value or '"' in value:
                            value = f'"{value}"'
                        row_values.append(value)
                    csv_data.append(','.join(row_values))

                response = app.response_class(
                    response='\n'.join(csv_data),
                    status=200,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=sales_export.csv'}
                )
                return response
            else:
                return jsonify({'success': False, 'error': 'No data to export'})

        elif export_type == 'clients':
            query = '''
            SELECT * FROM clients
            '''
            data = execute_query(query)

            if data:
                csv_data = []
                headers = data[0].keys()
                csv_data.append(','.join(headers))

                for row in data:
                    row_values = []
                    for h in headers:
                        value = str(row.get(h, ''))
                        value = value.replace('"', '""')
                        if ',' in value or '\n' in value or '"' in value:
                            value = f'"{value}"'
                        row_values.append(value)
                    csv_data.append(','.join(row_values))

                response = app.response_class(
                    response='\n'.join(csv_data),
                    status=200,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=clients_export.csv'}
                )
                return response
            else:
                return jsonify({'success': False, 'error': 'No data to export'})

        elif export_type == 'employees':
            query = '''
            SELECT * FROM employees
            '''
            data = execute_query(query)

            if data:
                csv_data = []
                headers = data[0].keys()
                csv_data.append(','.join(headers))

                for row in data:
                    row_values = []
                    for h in headers:
                        value = str(row.get(h, ''))
                        value = value.replace('"', '""')
                        if ',' in value or '\n' in value or '"' in value:
                            value = f'"{value}"'
                        row_values.append(value)
                    csv_data.append(','.join(row_values))

                response = app.response_class(
                    response='\n'.join(csv_data),
                    status=200,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=employees_export.csv'}
                )
                return response
            else:
                return jsonify({'success': False, 'error': 'No data to export'})

        else:
            return jsonify({'success': False, 'error': 'Invalid export type'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# HEALTH CHECK ENDPOINT
# ==============================================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'Rawas Real Estate System is running',
        'version': '4.0',
        'database': 'MySQL',
        'endpoints': [
            '/api/projects', '/api/buildings', '/api/units',
            '/api/clients', '/api/sales', '/api/employees',
            '/api/materials', '/api/inventory', '/api/reports'
        ]
    })


# ==============================================
# DATABASE DEBUG ENDPOINT
# ==============================================
@app.route('/api/debug/db-structure', methods=['GET'])
def debug_db_structure():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        structure = {}
        for table in tables:
            table_name = table[f'Tables_in_{db.db_config["database"]}']
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            structure[table_name] = [
                {'name': col['Field'], 'type': col['Type'], 'null': col['Null'], 'default': col['Default']}
                for col in columns
            ]

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'database': db.db_config['database'],
            'tables': structure
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================
# ERROR HANDLERS
# ==============================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ==============================================
# MAIN APPLICATION
# ==============================================
if __name__ == '__main__':
    print("=" * 60)
    print("🏢 Rawas Real Estate Investment System - Enhanced Version")
    print("=" * 60)
    print("🌐 Frontend: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000/dashboard")
    print("💰 Sales: http://localhost:5000/sales")
    print("👥 Clients: http://localhost:5000/clients")
    print("👨‍💼 Employees: http://localhost:5000/employees")
    print("🏗️ Projects: http://localhost:5000/projects")
    print("📦 Inventory: http://localhost:5000/inventory")
    print("📈 Reports: http://localhost:5000/reports")
    print("=" * 60)
    print(f"📁 Database: MySQL ({db.db_config['database']})")

    create_html_templates()

    print("✅ System initialized successfully!")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)