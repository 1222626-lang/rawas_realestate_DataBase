from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
app.secret_key = 'your-secret-key-here'

# البيانات التجريبية
projects_data = [
    {
        'id': 1,
        'name': 'جاردنز رام الله',
        'location': 'رام الله، حي المصيون',
        'start_date': '2024-01-15',
        'end_date': '2025-12-31',
        'status': 'Under Construction',
        'description': 'مشروع سكني فاخر يتكون من 4 أبراج',
        'created_at': '2024-03-15 10:30'
    },
    {
        'id': 2,
        'name': 'برج الخليل التجاري',
        'location': 'الخليل، وسط المدينة',
        'start_date': '2023-06-01',
        'end_date': '2024-11-30',
        'status': 'Completed',
        'description': 'برج تجاري يتكون من 10 طوابق',
        'created_at': '2023-06-01 09:00'
    }
]


# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('templates.html')


# صفحة المشاريع
@app.route('/project')
def project():
    return render_template('project.html', projects=projects_data)


# صفحة إضافة مشروع
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # معالجة بيانات النموذج
        new_project = {
            'id': len(projects_data) + 1,
            'name': request.form['name'],
            'location': request.form['location'],
            'start_date': request.form['start_date'],
            'end_date': request.form['end_date'] if request.form['end_date'] else None,
            'status': request.form['status'],
            'description': request.form['description'],
            'created_at': '2024-03-20 14:00'
        }
        projects_data.append(new_project)
        flash('تم إضافة المشروع بنجاح!', 'success')
        return redirect(url_for('project'))

    return render_template('add.html')


# صفحة عرض المشروع
@app.route('/view/<int:project_id>')
def view(project_id):
    project = next((p for p in projects_data if p['id'] == project_id), None)
    if not project:
        flash('المشروع غير موجود', 'error')
        return redirect(url_for('project'))

    # بيانات المباني التجريبية
    buildings = [
        {'building_number': 'B1', 'building_name': 'البرج الشمالي', 'floors_count': 8,
         'construction_status': 'Structure', 'completion_percentage': 60},
        {'building_number': 'B2', 'building_name': 'البرج الجنوبي', 'floors_count': 8,
         'construction_status': 'Foundation', 'completion_percentage': 30},
        {'building_number': 'B3', 'building_name': 'البرج الشرقي', 'floors_count': 6,
         'construction_status': 'Not Started', 'completion_percentage': 0}
    ]

    # إحصائيات
    statistics = {
        'total_buildings': 3,
        'total_units': 45,
        'sold_units': 12,
        'available_units': 33,
        'avg_completion': 30
    }

    return render_template('view.html',
                           project=project,
                           buildings=buildings,
                           statistics=statistics)


# صفحة تعديل المشروع
@app.route('/edit/<int:project_id>', methods=['GET', 'POST'])
def edit(project_id):
    project = next((p for p in projects_data if p['id'] == project_id), None)
    if not project:
        flash('المشروع غير موجود', 'error')
        return redirect(url_for('project'))

    if request.method == 'POST':
        # تحديث البيانات
        project['name'] = request.form['name']
        project['location'] = request.form['location']
        project['start_date'] = request.form['start_date']
        project['end_date'] = request.form['end_date'] if request.form['end_date'] else None
        project['status'] = request.form['status']
        project['description'] = request.form['description']

        flash('تم تحديث المشروع بنجاح!', 'success')
        return redirect(url_for('view', project_id=project_id))

    return render_template('edit.html', project=project)


# حذف المشروع
@app.route('/delete/<int:project_id>', methods=['POST'])
def delete(project_id):
    global projects_data
    projects_data = [p for p in projects_data if p['id'] != project_id]
    flash('تم حذف المشروع بنجاح!', 'success')
    return redirect(url_for('project'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)