from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return send_from_directory('.', 'interface.html')

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
    data = request.json
    name = data.get('name')
    role = data.get('role')
    uid = data.get('uid')

    if not name or not role or not uid:
        return jsonify({'success': False, 'error': 'Champs manquants'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO users (name, role, badgeuid) VALUES (?, ?, ?)', (name, role, uid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    uid = request.json.get('uid')
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE badgeuid = ?', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/rooms')
def get_rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])

@app.route('/api/add_room', methods=['POST'])
def add_room():
    data = request.json
    room_name = data.get('room_name')

    if not room_name:
        return jsonify({'error': 'Nom de salle manquant'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/update_hours', methods=['POST'])
def update_hours():
    data = request.json
    room_id = data.get('room_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not room_id or not start_time or not end_time:
        return jsonify({'error': 'Champs horaires manquants'}), 400

    conn = get_db_connection()
    conn.execute('DELETE FROM acces_horaire WHERE room_id = ?', (room_id,))
    conn.execute('INSERT INTO acces_horaire (room_id, start_time, end_time) VALUES (?, ?, ?)',
                 (room_id, start_time, end_time))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/room_status')
def room_status():
    conn = get_db_connection()
    now = datetime.now().strftime('%H:%M')
    query = """
        SELECT r.room_name, a.start_time, a.end_time
        FROM rooms r
        LEFT JOIN acces_horaire a ON r.id = a.room_id
    """
    rows = conn.execute(query).fetchall()
    conn.close()

    result = []
    for row in rows:
        if row['start_time'] and row['end_time']:
            if row['start_time'] <= now <= row['end_time']:
                status = 'Ouverte ✅'
            else:
                status = 'Fermée ❌'
        else:
            status = 'Pas d\'horaire ⏳'
        result.append({
            'room_name': row['room_name'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'status': status
        })

    return jsonify(result)

@app.route('/api/delete_room', methods=['POST'])
def delete_room():
    data = request.json
    room_id = data.get('room_id')
    if not room_id:
        return jsonify({'error': 'room_id manquant'}), 400

    conn = get_db_connection()
    conn.execute('DELETE FROM acces_horaire WHERE room_id = ?', (room_id,))
    conn.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
