from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return "Bienvenue sur l'API RFID hébergée sur Render"

@app.route('/check_badge', methods=['POST'])
def check_badge():
    uid = request.json.get('uid')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE badgeuid = ?', (uid,)).fetchone()
    conn.close()
    if user is None:
        return jsonify({'access': False, 'reason': 'Badge inconnu'}), 404
    return jsonify({'access': True, 'role': user['role'], 'name': user['name']}), 200

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    name = data.get('name')
    role = data.get('role')
    uid = data.get('uid')
    if not all([name, role, uid]):
        return jsonify({'success': False, 'reason': 'Données incomplètes'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute('SELECT * FROM users WHERE badgeuid = ?', (uid,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'reason': 'Badge déjà existant'}), 409

    cursor.execute('INSERT INTO users (name, role, badgeuid) VALUES (?, ?, ?)', (name, role, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    uid = data.get('uid')
    if not uid:
        return jsonify({'success': False, 'reason': 'UID manquant'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    deleted = cursor.execute('DELETE FROM users WHERE badgeuid = ?', (uid,))
    conn.commit()
    conn.close()
    if deleted.rowcount == 0:
        return jsonify({'success': False, 'reason': 'Badge introuvable'}), 404

    return jsonify({'success': True}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
