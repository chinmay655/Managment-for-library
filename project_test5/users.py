from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# This db object will be initialized in app.py
# db = SQLAlchemy(app)
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'user', or 'student'
    student_id = db.Column(db.String(30), unique=True, nullable=True)  # Only for students
    department = db.Column(db.String(80), nullable=True)  # Only for students
    year = db.Column(db.String(10), nullable=True)  # Only for students

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'

def create_initial_admin(db):
    """Create an initial admin user if none exists."""
    if not User.query.filter_by(role='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')  # Change this after first login!
        db.session.add(admin)
        db.session.commit()
        print('Initial admin user created: admin / admin123') 