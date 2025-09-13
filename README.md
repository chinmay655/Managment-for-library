📚 Library Management System

A Flask-based Library Management System that provides a web interface for managing books, members, borrowing/returning records, and attendance, with role-based authentication for Admin and User accounts.

✨ Features

➕ Add, update, and delete books and members
📖 Manage borrowing and returning of books
👥 Track attendance of members
🔑 Role-based authentication (Admin/User)
🌐 Clean and user-friendly web interface

🛠 Tech Stack

Backend: Python, Flask
Database: Flask-SQLAlchemy, SQLite/MySQL
Frontend: HTML, CSS, Bootstrap
Tools: VS Code, Git

🚀 Installation & Setup

1.Clone the repository:
git clone https://github.com/your-username/library-management-system.git
cd library-management-system

2.Create a virtual environment:
python -m venv venv
source venv/bin/activate   # On Mac/Linux  
venv\Scripts\activate      # On Windows

3.Install dependencies:
pip install -r requirements.txt

4.Run the Flask app:
flask run

📂 Project Structure
library-management-system/
│── app.py               # Main Flask application
│── models.py            # Database models
│── templates/           # HTML templates
│── static/              # CSS, JS, Images
│── requirements.txt     # Project dependencies
│── README.md            # Project documentation

