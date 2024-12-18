from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MySQL Configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Gre@ts#1*'
app.config['MYSQL_DB'] = 'lddb2'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')  # Landing page to choose login or register

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        admin_id = request.form.get('admin_id')  # For Manager
        manager_id = request.form.get('manager_id')  # For Employee

        cursor = mysql.connection.cursor()

        if role == 'Admin':
            cursor.execute('INSERT INTO Admins (Name, Email, Password) VALUES (%s, %s, %s)', (name, email, password))
        elif role == 'Manager':
            cursor.execute('INSERT INTO Managers (AdminID, Name, Email, Password) VALUES (%s, %s, %s, %s)', 
                           (admin_id, name, email, password))
        elif role == 'Employee':
            cursor.execute('INSERT INTO Employees (ManagerID, Name, Email, Password) VALUES (%s, %s, %s, %s)', 
                           (manager_id, name, email, password))

        mysql.connection.commit()
        cursor.close()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check Admin
        cursor.execute('SELECT * FROM Admins WHERE Name = %s AND Password = %s', (name, password))
        admin = cursor.fetchone()

        # Check Manager
        cursor.execute('SELECT * FROM Managers WHERE Name = %s AND Password = %s', (name, password))
        manager = cursor.fetchone()

        # Check Employee
        cursor.execute('SELECT * FROM Employees WHERE Name = %s AND Password = %s', (name, password))
        employee = cursor.fetchone()

        if admin:
            session['role'] = 'Admin'
            session['user_id'] = admin['AdminID']
            session['name'] = admin['Name']
            return redirect(url_for('admin_dashboard'))
        elif manager:
            session['role'] = 'Manager'
            session['user_id'] = manager['ManagerID']
            session['name'] = manager['Name']
            return redirect(url_for('manager_dashboard'))
        elif employee:
            session['role'] = 'Employee'
            session['user_id'] = employee['EmployeeID']
            session['name'] = employee['Name']
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# @app.route('/admin_dashboard')
# def admin_dashboard():
#     if 'role' in session and session['role'] == 'Admin':
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
#         # Get all course requests
#         cursor.execute('SELECT * FROM CourseRequests')
#         course_requests = cursor.fetchall()

#         # Count courses created by the admin
        # admin_id = session['user_id']  # Ensure you store admin_id in session
#         cursor.execute('SELECT COUNT(*) AS course_count FROM courses ')
#         courses_created = cursor.fetchone()['course_count']

#         # Count employees under the admin
#         cursor.execute('SELECT COUNT(*) AS employee_count FROM employees')
#         employees_count = cursor.fetchone()['employee_count']

#         # Count pending requests
#         cursor.execute("SELECT COUNT(*) AS pending_count FROM CourseRequests WHERE Status = 'Pending'")
#         pending_requests = cursor.fetchone()['pending_count']

#         cursor.execute('''
#             SELECT f.FeedbackID, f.Rating, f.Comments, f.SubmittedAt,
#                    e.Name AS EmployeeName, c.Title AS CourseTitle
#             FROM Feedback f
#             JOIN Assignments a ON f.AssignmentID = a.AssignmentID
#             JOIN Employees e ON f.EmployeeID = e.EmployeeID
#             JOIN Courses c ON a.CourseID = c.CourseID
#         ''')
#         feedbacks = cursor.fetchall()

#         return render_template(
#             'admin_dashboard.html',
#             course_requests=course_requests,
#             courses_created=courses_created,
#             employees_count=employees_count,
#             pending_requests=pending_requests,
#             feedbacks= feedbacks
#         )


#     return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'Admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Admin-specific information
        admin_id = session['user_id']
        
        # Fetch course requests
        cursor.execute('SELECT * FROM CourseRequests')
        course_requests = cursor.fetchall()

        # Count courses created by the admin
        cursor.execute('SELECT COUNT(*) AS course_count FROM courses')
        courses_created = cursor.fetchone()['course_count']

        # Count employees under the admin
        cursor.execute('SELECT COUNT(*) AS employee_count FROM employees ')
        employees_count = cursor.fetchone()['employee_count']

        # Count pending requests
        cursor.execute('SELECT COUNT(*) AS pending_count FROM CourseRequests WHERE Status = "Pending"')
        pending_requests = cursor.fetchone()['pending_count']

        # Fetch feedback specific to admin
        cursor.execute('''
            SELECT f.FeedbackID, f.Rating, f.Comments, f.SubmittedAt,
             e.Name AS EmployeeName, c.Title AS CourseTitle
            FROM Feedback f
            JOIN Assignments a ON f.AssignmentID = a.AssignmentID
            JOIN Employees e ON a.EmployeeID = e.EmployeeID
            JOIN Courses c ON a.CourseID = c.CourseID

        ''')
        feedbacks = cursor.fetchall()

        return render_template(
            'admin_dashboard.html',
            course_requests=course_requests,
            courses_created=courses_created,
            employees_count=employees_count,
            pending_requests=pending_requests,
            feedbacks=feedbacks
        )

    return redirect(url_for('login'))



@app.route('/manager_dashboard')
def manager_dashboard():
    if 'role' in session and session['role'] == 'Manager':
        manager_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get all course requests for the manager
        cursor.execute('SELECT * FROM CourseRequests WHERE ManagerID = %s', (manager_id,))
        requests = cursor.fetchall()

        # Get the approved and rejected requests
        approved_requests = [request for request in requests if request['Status'] == 'Approved']
        rejected_requests = [request for request in requests if request['Status'] == 'Rejected']
        pending_requests = [request for request in requests if request['Status'] == 'Pending']
        
        return render_template('manager_dashboard.html', 
                               requests=pending_requests, 
                               approved_requests=approved_requests, 
                               rejected_requests=rejected_requests)

    return redirect(url_for('login'))

from datetime import datetime

# @app.route('/employee_dashboard')
# def employee_dashboard():
#     if 'role' in session and session['role'] == 'Employee':
#         employee_id = session['user_id']
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

#         # Get assigned courses for the employee
#         cursor.execute(''' 
#             SELECT a.AssignmentID, a.EmployeeID, a.AssignedDate, c.Title, c.Link
#             FROM Assignments a
#             JOIN Courses c ON a.CourseID = c.CourseID
#             WHERE a.EmployeeID = %s
#         ''', (employee_id,))
        
#         assignments = cursor.fetchall()

#         # Format the AssignedDate before passing it to the template
#         for assignment in assignments:
#             if isinstance(assignment['AssignedDate'], datetime):
#                 assignment['AssignedDate'] = assignment['AssignedDate'].strftime('%B %d, %Y')  # Format as "Month Day, Year"
        
#         return render_template('employee_dashboard.html', assignments=assignments)
    
#     return redirect(url_for('login'))


@app.route('/employee_dashboard', methods=['GET', 'POST'])
def employee_dashboard():
    if 'role' in session and session['role'] == 'Employee':
        employee_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch assigned courses
        cursor.execute(''' 
            SELECT a.AssignmentID, a.EmployeeID, a.AssignedDate, a.Progress, c.Title, c.Link
            FROM Assignments a
            JOIN Courses c ON a.CourseID = c.CourseID
            WHERE a.EmployeeID = %s
        ''', (employee_id,))
        
        assignments = cursor.fetchall()

        # Format the AssignedDate before passing it to the template
        for assignment in assignments:
            if isinstance(assignment['AssignedDate'], datetime):
                assignment['AssignedDate'] = assignment['AssignedDate'].strftime('%B %d, %Y')  # Format as "Month Day, Year"

        return render_template('employee_dashboard.html', assignments=assignments)

    return redirect(url_for('login'))




@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/approve_request/<int:request_id>', methods=['GET', 'POST'])
def approve_request(request_id):
    if 'role' in session and session['role'] == 'Admin':
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE CourseRequests SET Status = %s WHERE RequestID = %s', ('Approved', request_id))
        mysql.connection.commit()
        flash('Request approved!', 'success')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/reject_request/<int:request_id>', methods=['GET', 'POST'])
def reject_request(request_id):
    if 'role' in session and session['role'] == 'Admin':
        cursor = mysql.connection.cursor()
        
        # Reject the request
        cursor.execute('UPDATE CourseRequests SET Status = %s WHERE RequestID = %s', ('Rejected', request_id))
        mysql.connection.commit()
        
        flash('Request rejected.', 'danger')
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/assign_course', methods=['GET', 'POST'])
def assign_course():
    if 'role' in session and session['role'] == 'Admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch all available courses (from Courses table) to assign
        cursor.execute('SELECT * FROM Courses')
        courses = cursor.fetchall()

        if request.method == 'POST':
            # Get selected employee and course details
            selected_employee = request.form.get('employee_id')
            selected_course = request.form.get('course_id')

            if not selected_employee or not selected_course:
                flash('Please select both an employee and a course to assign.', 'warning')
                return redirect(url_for('assign_course'))

            # Assign the selected course to the employee
            try:
                cursor.execute('INSERT INTO Assignments (CourseID, EmployeeID, AssignedDate) VALUES (%s, %s, %s)', 
                               (selected_course, selected_employee, datetime.now()))
                mysql.connection.commit()

                flash('Course successfully assigned to the employee!', 'success')
                return redirect(url_for('admin_dashboard'))

            except Exception as e:
                mysql.connection.rollback()
                flash('An error occurred while assigning the course. Please try again.', 'danger')
                return redirect(url_for('admin_dashboard'))

        # Fetch all employees for selection
        cursor.execute('SELECT EmployeeID, Name FROM Employees')
        employees = cursor.fetchall()

        return render_template('assign_course.html', courses=courses, employees=employees)
    
    return redirect(url_for('login'))



@app.route('/submit_course_request', methods=['GET', 'POST'])
def submit_course_request():
    if 'role' in session and session['role'] == 'Manager':
        if request.method == 'POST':
            course_title = request.form['course_title']
            description = request.form['description']
            manager_id = session['user_id']  # Assuming manager's ID is stored in session

            cursor = mysql.connection.cursor()

            # Insert the course request into the database
            cursor.execute('INSERT INTO CourseRequests (ManagerID, CourseTitle, Description) VALUES (%s, %s, %s)',
                           (manager_id, course_title, description))
            mysql.connection.commit()

            flash('Course request submitted successfully and is pending approval.', 'success')
            return redirect(url_for('manager_dashboard'))

    return redirect(url_for('login'))


@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if 'role' in session and session['role'] == 'Admin':
        if request.method == 'POST':
            # Collect course details from the form
            course_title = request.form['course_title']
            description = request.form['description']
            link = request.form['link']

            # Insert the new course into the Courses table
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO Courses (Title, Description, Link) VALUES (%s, %s, %s)', 
                           (course_title, description, link))
            mysql.connection.commit()
            flash('Course created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        return render_template('create_course.html')  # Render a form for course creation
    return redirect(url_for('login'))
    
@app.route('/employee_progress')
def employee_progress():
    if 'role' in session and session['role'] == 'Admin':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Get progress data of all employees
        cursor.execute('''
            SELECT e.Name AS EmployeeName, c.Title AS CourseName, a.AssignedDate, a.Progress
            FROM Assignments a
            JOIN Employees e ON a.EmployeeID = e.EmployeeID
            JOIN Courses c ON a.CourseID = c.CourseID
        ''')
        progress_data = cursor.fetchall()

        return render_template('employee_progress.html', progress_data=progress_data)
    
    return redirect(url_for('login'))

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    # Ensure the user is logged in and is an employee
    if 'role' in session and session['role'] == 'Employee':
        # Retrieve the EmployeeID from the session
        employee_id = session.get('user_id')

        # If EmployeeID is not in session, retrieve it using the user's email
        if not employee_id:
            user_email = session.get('email')  # Assuming email is stored in the session
            cursor = mysql.connection.cursor()
            cursor.execute(''' 
                SELECT EmployeeID
                FROM Employees 
                WHERE Email = %s
            ''', (user_email,))
            result = cursor.fetchone()
            if result:
                employee_id = result[0]
                session['user_id'] = employee_id  # Store it back in session for future use
            else:
                flash('Error: Unable to identify employee. Please try again.', 'danger')
                return redirect(url_for('employee_dashboard'))

        # Now that we have the EmployeeID, proceed to get the feedback details from the form
        assignment_id = request.form['assignment_id']
        rating = request.form['rating']
        comments = request.form.get('comments', '')

        # Insert the feedback into the database
        cursor = mysql.connection.cursor()
        cursor.execute(''' 
            INSERT INTO Feedback (AssignmentID, EmployeeID, Rating, Comments) 
            VALUES (%s, %s, %s, %s)
        ''', (assignment_id, employee_id, rating, comments))
        mysql.connection.commit()
        cursor.close()

        flash('Feedback submitted successfully!', 'success')
    else:
        flash('You are not authorized to submit feedback.', 'danger')

    return redirect(url_for('employee_dashboard'))



@app.route('/update_course', methods=['POST'])
def update_course():
    # Extract data from the form
    assignment_id = request.form.get('assignment_id')
    status = request.form.get('status')

    # Determine the progress value based on the status
    if status == "Started":
        progress = 50  # Example: Started implies 50% progress
    elif status == "Completed":
        progress = 100  # Completed implies 100% progress
    else:
        progress = 0  # Default for other statuses

    # Update the assignments table
    query = """
        UPDATE assignments
        SET Progress = %s
        WHERE AssignmentID = %s
    """
    try:
        cursor = mysql.connection.cursor()  # Assuming you're using MySQL
        cursor.execute(query, (progress, assignment_id))
        mysql.connection.commit()
        cursor.close()
        flash("Course progress updated successfully!", "success")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error updating course progress: {e}", "danger")
        print(f"Error: {e}")

    return redirect(url_for('employee_dashboard'))  # Redirect back to the dashboard



def get_all_employees():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM Employees')  # Assuming you have an Employees table
    employees = cursor.fetchall()
    cursor.close()
    return employees

if __name__ == '__main__':
    app.run(debug=True)
