from flask import Flask, request, jsonify, g
import sqlite3
import json
import re

app = Flask(__name__)

def get_db():
    """Get a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect('users.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

# --- Database Logic ---
def fetch_all_users():
    db = get_db()
    cursor = db.execute("SELECT * FROM users")
    return [dict(u) for u in cursor.fetchall()]

def fetch_user_by_id(user_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return dict(user) if user else None

def insert_user(name, email, password):
    db = get_db()
    db.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
    db.commit()

def update_user_by_id(user_id, name, email):
    db = get_db()
    db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user_id))
    db.commit()

def delete_user_by_id(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

def search_users_by_name(name):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE name LIKE ?", (f"%{name}%",))
    return [dict(u) for u in cursor.fetchall()]

def authenticate_user(email, password):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    return dict(user) if user else None

def is_valid_email(email):
    """Simple email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_password(password):
    """Password must be at least 6 characters."""
    return isinstance(password, str) and len(password) >= 6

# --- Routes ---
@app.route('/')
def home():
    """Home endpoint."""
    return jsonify({"message": "User Management System"}), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = fetch_all_users()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = fetch_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('name', 'email', 'password')):
            return jsonify({"error": "Missing required fields"}), 400
        name = data['name']
        email = data['email']
        password = data['password']
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        if not is_valid_password(password):
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        insert_user(name, email, password)
        return jsonify({"message": "User created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('name', 'email')):
            return jsonify({"error": "Missing required fields"}), 400
        name = data.get('name')
        email = data.get('email')
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        update_user_by_id(user_id, name, email)
        return jsonify({"message": "User updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        delete_user_by_id(user_id)
        return jsonify({"message": f"User {user_id} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['GET'])
def search_users():
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({"error": "Please provide a name to search"}), 400
        users = search_users_by_name(name)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({"error": "Missing required fields"}), 400
        email = data['email']
        password = data['password']
        user = authenticate_user(email, password)
        if user:
            return jsonify({"status": "success", "user_id": user['id']}), 200
        else:
            return jsonify({"status": "failed"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)