import mysql.connector
from mysql.connector import Error
from flask import g
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Database:
    """
    Database connection manager for MySQL
    """

    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '3306'),
            'database': os.getenv('DB_NAME', 'rawas_realestate'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '')
        }

    def get_connection(self):
        """
        Create and return database connection
        """
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Execute SQL query
        """
        connection = None
        cursor = None

        try:
            connection = self.get_connection()
            if connection is None:
                return None

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if commit:
                connection.commit()
                return cursor.lastrowid

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()

            return None

        except Error as e:
            print(f"Database error: {e}")
            return None

        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    # Project-related queries
    def get_all_projects(self):
        """Get all projects"""
        query = """
            SELECT * FROM Projects 
            ORDER BY created_at DESC
        """
        return self.execute_query(query, fetch_all=True)

    def get_project_by_id(self, project_id):
        """Get single project by ID"""
        query = """
            SELECT * FROM Projects 
            WHERE project_id = %s
        """
        return self.execute_query(query, (project_id,), fetch_one=True)

    def add_project(self, name, location, start_date, end_date, status, description):
        """Add new project"""
        query = """
            INSERT INTO Projects (name, location, start_date, end_date, status, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (name, location, start_date, end_date, status, description)
        return self.execute_query(query, params, commit=True)

    def update_project(self, project_id, name, location, start_date, end_date, status, description):
        """Update existing project"""
        query = """
            UPDATE Projects 
            SET name = %s, location = %s, start_date = %s, 
                end_date = %s, status = %s, description = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_id = %s
        """
        params = (name, location, start_date, end_date, status, description, project_id)
        return self.execute_query(query, params, commit=True)

    def delete_project(self, project_id):
        """Delete project"""
        query = "DELETE FROM Projects WHERE project_id = %s"
        return self.execute_query(query, (project_id,), commit=True)

    # Building-related queries
    def get_buildings_by_project(self, project_id):
        """Get all buildings for a project"""
        query = """
            SELECT * FROM Buildings 
            WHERE project_id = %s 
            ORDER BY building_number
        """
        return self.execute_query(query, (project_id,), fetch_all=True)

    def get_project_statistics(self, project_id):
        """Get statistics for a project"""
        query = """
            SELECT 
                COUNT(DISTINCT b.building_id) as total_buildings,
                COUNT(DISTINCT u.unit_id) as total_units,
                SUM(CASE WHEN u.status = 'Sold' THEN 1 ELSE 0 END) as sold_units,
                SUM(CASE WHEN u.status = 'Available' THEN 1 ELSE 0 END) as available_units,
                AVG(b.completion_percentage) as avg_completion
            FROM Projects p
            LEFT JOIN Buildings b ON p.project_id = b.project_id
            LEFT JOIN Units u ON b.building_id = u.building_id
            WHERE p.project_id = %s
            GROUP BY p.project_id
        """
        return self.execute_query(query, (project_id,), fetch_one=True)


# Create database instance
db = Database()