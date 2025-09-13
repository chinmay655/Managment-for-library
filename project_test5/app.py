from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from users import db, User, create_initial_admin
from library import Library
from datetime import datetime, date, timedelta
import os
from functools import wraps
from flask_migrate import Migrate  # type: ignore # Added for migrations
import csv
from io import TextIOWrapper

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)  # Added for migrations

with app.app_context():
    db.create_all()
    create_initial_admin(db)

# Initialize the main Library object
the_library = Library()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Protect main features (books, members, attendance, borrow, return)
@app.route('/')
@login_required
def home():
    stats = the_library.get_library_stats()
    return render_template('home.html', stats=stats)

# --- Book Management ---
@app.route('/books')
@login_required
def books():
    books = the_library.list_all_books()
    return render_template('books.html', books=books)

@app.route('/add_book', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        category = request.form.get('category', 'General')
        copies = int(request.form.get('copies', 1))
        if the_library.add_book(book_id, title, author, isbn, category, copies):
            flash('Book added successfully!', 'success')
            return redirect(url_for('books'))
        else:
            flash('Book ID already exists.', 'danger')
    return render_template('add_book.html')

# --- Member Management ---
@app.route('/members')
@login_required
def members():
    members = the_library.list_all_members()
    return render_template('members.html', members=members)

@app.route('/add_member', methods=['GET', 'POST'])
@admin_required
def add_member():
    if request.method == 'POST':
        member_id = request.form['member_id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        membership_type = request.form.get('membership_type', 'Regular')
        if the_library.add_member(member_id, name, email, phone, membership_type):
            flash('Member added successfully!', 'success')
            return redirect(url_for('members'))
        else:
            flash('Member ID already exists.', 'danger')
    return render_template('add_member.html')

# --- Borrow/Return Books ---
@app.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow():
    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        if the_library.borrow_book(member_id, book_id):
            flash('Book borrowed successfully!', 'success')
        else:
            flash('Failed to borrow book. Check member/book availability.', 'danger')
        return redirect(url_for('books'))
    members = the_library.list_all_members()
    books = the_library.list_available_books()
    return render_template('borrow.html', members=members, books=books)

@app.route('/return', methods=['GET', 'POST'])
@login_required
def return_book():
    if request.method == 'POST':
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        if the_library.return_book(member_id, book_id):
            flash('Book returned successfully!', 'success')
        else:
            flash('Failed to return book.', 'danger')
        return redirect(url_for('books'))
    members = the_library.list_all_members()
    books = the_library.list_all_books()
    return render_template('return.html', members=members, books=books)

# --- Attendance Management ---
@app.route('/attendance')
@login_required
def attendance():
    today = date.today()
    stats = the_library.get_daily_attendance_stats(today)
    visitors = the_library.get_current_visitors()
    return render_template('attendance.html', stats=stats, visitors=visitors)

@app.route('/check_in', methods=['GET', 'POST'])
@login_required
def check_in():
    if request.method == 'POST':
        visitor_type = request.form['visitor_type']
        visitor_id = request.form['visitor_id']
        name = request.form['name']
        purpose = request.form.get('purpose', '')
        if visitor_type == 'member':
            success = the_library.check_in_member(visitor_id)
        elif visitor_type == 'visitor':
            success = the_library.check_in_visitor(visitor_id, name, purpose)
        elif visitor_type == 'staff':
            success = the_library.check_in_staff(visitor_id, name)
        else:
            success = False
        if success:
            flash('Check-in successful!', 'success')
        else:
            flash('Check-in failed. Already checked in or invalid ID.', 'danger')
        return redirect(url_for('attendance'))
    return render_template('check_in.html')

@app.route('/check_out', methods=['POST'])
@login_required
def check_out():
    visitor_id = request.form['visitor_id']
    if the_library.check_out(visitor_id):
        flash('Check-out successful!', 'success')
    else:
        flash('Check-out failed. Not found or already checked out.', 'danger')
    return redirect(url_for('attendance'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if user.role != 'admin':
                flash('Only admins are allowed to log in.', 'danger')
                return render_template('login.html')
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/users')
@admin_required
def users():
    user_list = User.query.all()
    return render_template('users.html', users=user_list)

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        student_id = request.form.get('student_id')
        department = request.form.get('department')
        year = request.form.get('year')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
        elif role == 'student' and student_id and User.query.filter_by(student_id=student_id).first():
            flash('Student ID already registered.', 'danger')
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            if role == 'student':
                new_user.student_id = student_id
                new_user.department = department
                new_user.year = year
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('users'))
    return render_template('add_user.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == session.get('username'):
        flash('You cannot delete your own account.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    return redirect(url_for('users'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    flash('Registration is disabled. Only admins can have accounts.', 'warning')
    return redirect(url_for('login'))

@app.route('/import_students', methods=['GET', 'POST'])
@admin_required
def import_students():
    results = []
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file.', 'danger')
            return render_template('import_students.html', results=results)
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        for row in reader:
            username = row.get('username')
            password = row.get('password')
            student_id = row.get('student_id')
            department = row.get('department')
            year = row.get('year')
            if not username or not password or not student_id:
                results.append({'username': username, 'student_id': student_id, 'status': 'Missing required fields'})
                continue
            if User.query.filter_by(username=username).first():
                results.append({'username': username, 'student_id': student_id, 'status': 'Username exists'})
                continue
            if User.query.filter_by(student_id=student_id).first():
                results.append({'username': username, 'student_id': student_id, 'status': 'Student ID exists'})
                continue
            new_user = User(username=username, role='student', student_id=student_id, department=department, year=year)
            new_user.set_password(password)
            db.session.add(new_user)
            results.append({'username': username, 'student_id': student_id, 'status': 'Imported'})
        db.session.commit()
        flash('Import completed.', 'success')
    return render_template('import_students.html', results=results)

@app.route('/import_books', methods=['GET', 'POST'])
@admin_required
def import_books():
    results = []
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid CSV file.', 'danger')
            return render_template('import_books.html', results=results)
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        for row in reader:
            book_id = row.get('book_id')
            title = row.get('title')
            author = row.get('author')
            isbn = row.get('isbn')
            category = row.get('category', 'General')
            copies = row.get('copies', 1)
            try:
                copies = int(copies)
            except Exception:
                copies = 1
            if not book_id or not title or not author or not isbn:
                results.append({'book_id': book_id, 'title': title, 'status': 'Missing required fields'})
                continue
            if not the_library.add_book(book_id, title, author, isbn, category, copies):
                results.append({'book_id': book_id, 'title': title, 'status': 'Book ID exists'})
                continue
            results.append({'book_id': book_id, 'title': title, 'status': 'Imported'})
        flash('Import completed.', 'success')
    return render_template('import_books.html', results=results)

@app.route('/admin/data_management')
@admin_required
def admin_data_management():
    return render_template('admin/data_management.html')

@app.route('/admin/users_data')
@admin_required
def admin_users_data():
    """Admin view of all users data."""
    users = User.query.all()
    user_stats = {
        'total': len(users),
        'admins': len([u for u in users if u.role == 'admin']),
        'students': len([u for u in users if u.role == 'student']),
        'staff': len([u for u in users if u.role == 'user'])
    }
    return render_template('admin/users_data.html', users=users, stats=user_stats)

@app.route('/admin/books_data')
@admin_required
def admin_books_data():
    """Admin view of all books data."""
    books = the_library.list_all_books()
    book_stats = {
        'total_books': len(books),
        'total_copies': sum(book.total_copies for book in books),
        'available_copies': sum(book.available_copies for book in books),
        'borrowed_copies': sum(book.total_copies - book.available_copies for book in books),
        'categories': len(set(book.category for book in books))
    }
    return render_template('admin/books_data.html', books=books, stats=book_stats)

@app.route('/admin/members_data')
@admin_required
def admin_members_data():
    """Admin view of all members data."""
    members = the_library.list_all_members()
    member_stats = {
        'total_members': len(members),
        'active_members': len([m for m in members if m.borrowed_books]),
        'premium_members': len([m for m in members if m.membership_type == 'Premium']),
        'regular_members': len([m for m in members if m.membership_type == 'Regular'])
    }
    return render_template('admin/members_data.html', members=members, stats=member_stats)

@app.route('/admin/attendance_data')
@admin_required
def admin_attendance_data():
    """Admin view of attendance data."""
    today = date.today()
    current_visitors = the_library.get_current_visitors()
    daily_stats = the_library.get_daily_attendance_stats(today)
    
    # Get attendance history for the last 7 days
    attendance_history = []
    for i in range(7):
        check_date = today - timedelta(days=i)
        stats = the_library.get_daily_attendance_stats(check_date)
        attendance_history.append({
            'date': check_date,
            'stats': stats
        })
    
    return render_template('admin/attendance_data.html', 
                         current_visitors=current_visitors,
                         daily_stats=daily_stats,
                         attendance_history=attendance_history)

@app.route('/admin/transactions_data')
@admin_required
def admin_transactions_data():
    """Admin view of transaction history."""
    transactions = the_library.get_transaction_history(100)  # Last 100 transactions
    return render_template('admin/transactions_data.html', transactions=transactions)

@app.route('/admin/overdue_data')
@admin_required
def admin_overdue_data():
    """Admin view of overdue books."""
    overdue_books = the_library.get_overdue_books(14)  # Books overdue for 14+ days
    return render_template('admin/overdue_data.html', overdue_books=overdue_books)

@app.route('/admin/export_data/<data_type>')
@admin_required
def admin_export_data(data_type):
    """Export data as CSV."""
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.writer(output)
    
    if data_type == 'users':
        users = User.query.all()
        writer.writerow(['ID', 'Username', 'Role', 'Student ID', 'Department', 'Year'])
        for user in users:
            writer.writerow([user.id, user.username, user.role, user.student_id, user.department, user.year])
    
    elif data_type == 'books':
        books = the_library.list_all_books()
        writer.writerow(['Book ID', 'Title', 'Author', 'ISBN', 'Category', 'Total Copies', 'Available Copies'])
        for book in books:
            writer.writerow([book.book_id, book.title, book.author, book.isbn, book.category, book.total_copies, book.available_copies])
    
    elif data_type == 'members':
        members = the_library.list_all_members()
        writer.writerow(['Member ID', 'Name', 'Email', 'Phone', 'Membership Type', 'Join Date', 'Borrowed Books'])
        for member in members:
            writer.writerow([member.member_id, member.name, member.email, member.phone, member.membership_type, member.join_date, len(member.borrowed_books)])
    
    elif data_type == 'attendance':
        # Export today's attendance
        today = date.today()
        attendance_records = the_library.attendance_tracker.get_daily_attendance(today)
        writer.writerow(['Visitor ID', 'Name', 'Type', 'Entry Time', 'Exit Time', 'Duration (min)', 'Purpose'])
        for record in attendance_records:
            writer.writerow([record.visitor_id, record.name, record.visitor_type.value, 
                           record.entry_time, record.exit_time, record.get_duration(), record.purpose])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={data_type}_data_{date.today()}.csv'}
    )

@app.route('/admin/search_data', methods=['GET', 'POST'])
@admin_required
def admin_search_data():
    """Advanced search functionality for admin."""
    results = {}
    search_query = request.form.get('search_query', '')
    search_type = request.form.get('search_type', 'all')
    
    if request.method == 'POST' and search_query:
        if search_type in ['all', 'users']:
            users = User.query.filter(
                (User.username.contains(search_query)) |
                (User.student_id.contains(search_query)) |
                (User.department.contains(search_query))
            ).all()
            results['users'] = users
        
        if search_type in ['all', 'books']:
            books = the_library.search_books(search_query, 'title')
            books.extend(the_library.search_books(search_query, 'author'))
            books.extend(the_library.search_books(search_query, 'isbn'))
            results['books'] = list(set(books))  # Remove duplicates
        
        if search_type in ['all', 'members']:
            members = [m for m in the_library.list_all_members() 
                      if search_query.lower() in m.name.lower() or 
                         search_query.lower() in m.email.lower() or
                         search_query in m.member_id]
            results['members'] = members
    
    return render_template('admin/search_data.html', results=results, search_query=search_query, search_type=search_type)

if __name__ == '__main__':
    app.run(debug=True)

# Migration commands (run in terminal):
# flask db init         # Only once, to initialize migrations
# flask db migrate -m "Describe changes"
# flask db upgrade 