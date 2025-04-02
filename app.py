from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import logging

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def web_interface():
    return send_from_directory('.', 'interface.html')

@app.route('/check_badge', methods=['POST'])
def check_badge():
    uid = request.json.get('uid')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE badgeuid = ?', (uid,)).fetchone()
    conn.close()

    if user is None:
        app.logger.info(f"[CHECK_BADGE] UID inconnu : {uid}")
        return jsonify({'access': False, 'reason': 'Badge inconnu'}), 404

    app.logger.info(f"[CHECK_BADGE] UID reconnu : {uid} - Utilisateur : {user['name']} - Rôle : {user['role']}")
    return jsonify({'access': True, 'role': user['role'], 'name': user['name']}), 200

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    uid = data.get('uid')

    if not name or not role or not uid:
        app.logger.warning("[ADD_USER] Données manquantes.")
        return jsonify({'error': 'Champs manquants'}), 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (name, role, badgeuid) VALUES (?, ?, ?)', (name, role, uid))
        conn.commit()
        app.logger.info(f"[ADD_USER] Utilisateur ajouté : {name} ({role}) - UID: {uid}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"[ADD_USER] Erreur : {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    uid = request.json.get('uid')
    if not uid:
        app.logger.warning("[DELETE_USER] UID manquant.")
        return jsonify({'error': 'UID manquant'}), 400

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM users WHERE badgeuid = ?', (uid,))
        conn.commit()
        app.logger.info(f"[DELETE_USER] Utilisateur supprimé - UID: {uid}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"[DELETE_USER] Erreur : {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/add_room', methods=['POST'])
def add_room():
    room_name = request.json.get('room_name')
    if not room_name:
        app.logger.warning("[ADD_ROOM] Nom de salle manquant.")
        return jsonify({'error': 'Nom de salle manquant'}), 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
        conn.commit()
        app.logger.info(f"[ADD_ROOM] Salle ajoutée : {room_name}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"[ADD_ROOM] Erreur : {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/rooms')
def get_rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])

@app.route('/api/update_hours', methods=['POST'])
def update_hours():
    data = request.json
    room_id = data.get('room_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    conn = get_db_connection()
    try:
        conn.execute('REPLACE INTO acces_horaire (room_id, start_time, end_time) VALUES (?, ?, ?)',
                     (room_id, start_time, end_time))
        conn.commit()
        app.logger.info(f"[UPDATE_HOURS] Salle ID: {room_id} - {start_time} à {end_time}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"[UPDATE_HOURS] Erreur : {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/room_status')
def room_status():
    conn = get_db_connection()
    query = '''
        SELECT rooms.id, rooms.room_name, acces_horaire.start_time, acces_horaire.end_time,
            CASE
                WHEN time('now', 'localtime') BETWEEN acces_horaire.start_time AND acces_horaire.end_time THEN 'Ouverte'
                ELSE 'Fermée'
            END AS status
        FROM rooms
        LEFT JOIN acces_horaire ON rooms.id = acces_horaire.room_id
    '''
    rooms = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])

@app.route('/api/delete_room', methods=['POST'])
def delete_room():
    data = request.json
    room_id = data.get('room_id')
    if not room_id:
        app.logger.warning("[DELETE_ROOM] room_id manquant.")
        return jsonify({'error': 'room_id manquant'}), 400

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM acces_horaire WHERE room_id = ?', (room_id,))
        conn.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
        conn.commit()
        app.logger.info(f"[DELETE_ROOM] Salle supprimée - ID: {room_id}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"[DELETE_ROOM] Erreur : {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')