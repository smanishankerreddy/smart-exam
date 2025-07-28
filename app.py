from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Path to the SQLite DB
DB_FILE = 'exam.db'

# Create DB and table if not exists
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT UNIQUE,
                login_time TEXT
            )
        ''')
        conn.commit()

# Serve login.html (root route)
@app.route('/')
def login_page():
    return send_from_directory('static', 'login.html')

# Serve exam.html after login
@app.route('/exam')
def exam_page():
    return send_from_directory('static', 'index.html')

# Serve static files like JS, CSS
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# API to handle login logic
@app.route('/login', methods=['POST'])
def login():
    reg_no = request.json.get('reg_no')

    if not reg_no:
        return jsonify({'status': 'error', 'message': 'Register number is required'}), 400

    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            # Check if RegNo already logged
            cursor.execute("SELECT * FROM users WHERE reg_no = ?", (reg_no,))
            user = cursor.fetchone()

            if user:
                return jsonify({'status': 'denied', 'message': 'Already attempted'}), 403

            # Insert new login
            login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO users (reg_no, login_time) VALUES (?, ?)", (reg_no, login_time))
            conn.commit()

            return jsonify({'status': 'allowed', 'message': 'Login successful'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

# Run app
if __name__ == '__main__':
    init_db()  # Ensure DB is ready
    app.run(debug=True)
