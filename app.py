from flask import Flask, render_template, request, redirect, url_for, flash
import os

# Create Flask application
app = Flask(__name__,
            template_folder='templates',  # Folder for HTML files
            static_folder='static')  # Folder for CSS/JS/images
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Sample data for testing (temporary database)
projects_data = [
    {
        'id': 1,
        'name': 'Ramallah Gardens',
        'location': 'Ramallah, Al-Masyoun',
        'start_date': '2024-01-15',
        'end_date': '2025-12-31',
        'status': 'Under Construction',
        'description': 'Luxury residential project with 4 towers',
        'created_at': '2024-03-15 10:30'
    },
    {
        'id': 2,
        'name': 'Hebron Commercial Tower',
        'location': 'Hebron, City Center',
        'start_date': '2023-06-01',
        'end_date': '2024-11-30',
        'status': 'Completed',
        'description': '10-floor commercial tower for offices and shops',
        'created_at': '2023-06-01 09:00'
    }
]


# ============================
# ROUTES (URL ENDPOINTS)
# ============================

# Route 1: Home Page
@app.route('/')
def index():
    """
    Home page - renders the main template
    """
    return render_template('templates.html')


# Route 2: Projects List Page
@app.route('/project')
def project():
    """
    Display all projects in a list
    """
    return render_template('project.html', projects=projects_data)


# Route 3: Add New Project Page
@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Add new project - handles both form display (GET) and form submission (POST)
    """
    if request.method == 'POST':
        # Get form data
        new_project = {
            'id': len(projects_data) + 1,  # Auto-increment ID
            'name': request.form['name'],
            'location': request.form['location'],
            'start_date': request.form['start_date'],
            'end_date': request.form['end_date'] if request.form['end_date'] else None,
            'status': request.form['status'],
            'description': request.form['description'],
            'created_at': '2024-03-20 14:00'  # Current timestamp
        }

        # Add to projects list
        projects_data.append(new_project)

        # Show success message
        flash('Project added successfully!', 'success')

        # Redirect to projects list
        return redirect(url_for('project'))

    # If GET request, show the form
    return render_template('add.html')


# Route 4: View Project Details
@app.route('/view/<int:project_id>')
def view(project_id):
    """
    View details of a specific project
    project_id: ID from URL
    """
    # Find project by ID
    project = next((p for p in projects_data if p['id'] == project_id), None)

    # If project not found
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('project'))

    # Sample buildings data (for testing)
    buildings = [
        {'building_number': 'B1', 'building_name': 'North Tower', 'floors_count': 8,
         'construction_status': 'Structure', 'completion_percentage': 60},
        {'building_number': 'B2', 'building_name': 'South Tower', 'floors_count': 8,
         'construction_status': 'Foundation', 'completion_percentage': 30},
        {'building_number': 'B3', 'building_name': 'East Tower', 'floors_count': 6,
         'construction_status': 'Not Started', 'completion_percentage': 0}
    ]

    # Sample statistics (for testing)
    statistics = {
        'total_buildings': 3,
        'total_units': 45,
        'sold_units': 12,
        'available_units': 33,
        'avg_completion': 30
    }

    # Render view page with all data
    return render_template('view.html',
                           project=project,
                           buildings=buildings,
                           statistics=statistics)


# Route 5: Edit Project
@app.route('/edit/<int:project_id>', methods=['GET', 'POST'])
def edit(project_id):
    """
    Edit existing project
    """
    # Find project by ID
    project = next((p for p in projects_data if p['id'] == project_id), None)

    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('project'))

    if request.method == 'POST':
        # Update project data from form
        project['name'] = request.form['name']
        project['location'] = request.form['location']
        project['start_date'] = request.form['start_date']
        project['end_date'] = request.form['end_date'] if request.form['end_date'] else None
        project['status'] = request.form['status']
        project['description'] = request.form['description']

        # Show success message
        flash('Project updated successfully!', 'success')

        # Redirect to project view
        return redirect(url_for('view', project_id=project_id))

    # If GET request, show edit form with current data
    return render_template('edit.html', project=project)


# Route 6: Delete Project
@app.route('/delete/<int:project_id>', methods=['POST'])
def delete(project_id):
    """
    Delete a project (POST only for security)
    """
    global projects_data

    # Remove project from list
    projects_data = [p for p in projects_data if p['id'] != project_id]

    # Show success message
    flash('Project deleted successfully!', 'success')

    # Redirect to projects list
    return redirect(url_for('project'))


# Route 7: Dashboard (optional)
@app.route('/dashboard')
def dashboard():
    """
    Dashboard with statistics
    """
    # Calculate statistics
    total_projects = len(projects_data)
    completed_projects = len([p for p in projects_data if p['status'] == 'Completed'])
    ongoing_projects = len([p for p in projects_data if p['status'] == 'Under Construction'])

    stats = {
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects,
        'completion_rate': (completed_projects / total_projects * 100) if total_projects > 0 else 0
    }

    return render_template('dashboard.html', stats=stats)


# Run the application
if __name__ == '__main__':
    # Start Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)