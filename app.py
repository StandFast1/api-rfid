from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def web_interface():
    return send_from_directory('.', 'interface.html')

@app.route('/api/rooms')
def get_rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])

@app.route('/api/add_room', methods=['POST'])
def add_room():
    data = request.get_json()
    room_name = data.get('room_name')

    if not room_name:
        return jsonify({'error': 'Nom de salle manquant'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

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

@app.route('/api/add_room', methods=['POST'])
def add_room():
    data = request.get_json()
    room_name = data.get('room_name')

    if not room_name:
        return jsonify({'error': 'Nom de salle requis'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
