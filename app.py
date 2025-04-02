from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Connexion à la base de données
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Page d'accueil avec l'interface HTML
@app.route('/')
def web_interface():
    return send_from_directory('.', 'interface.html')


# Vérification badge
@app.route('/check_badge', methods=['POST'])
def check_badge():
    uid = request.json.get('uid')
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE badgeuid = ?', (uid,)).fetchone()
    conn.close()

    if user is None:
        return jsonify({'access': False, 'reason': 'Badge inconnu'}), 404

    return jsonify({
        'access': True,
        'role': user['role'],
        'name': user['name']
    }), 200


# Ajouter un utilisateur
@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    uid = data.get('uid')
    
    if not name or not role or not uid:
        return jsonify({'error': 'Champs manquants'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO users (name, role, badgeuid) VALUES (?, ?, ?)', (name, role, uid))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# Supprimer un utilisateur
@app.route('/delete_user', methods=['POST'])
def delete_user():
    uid = request.json.get('uid')

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE badgeuid = ?', (uid,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# Récupérer tous les utilisateurs
@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT name, role, badgeuid FROM users').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])


# Récupérer toutes les salles
@app.route('/api/rooms')
def get_rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rooms])


# Ajouter une salle (⚠️ renommée ici)
@app.route('/api/add_room', methods=['POST'])
def api_add_room():
    data = request.json
    room_name = data.get('room_name')

    if not room_name:
        return jsonify({'error': 'Nom de salle manquant'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO rooms (room_name) VALUES (?)', (room_name,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# Modifier les horaires d'accès
@app.route('/api/update_hours', methods=['POST'])
def update_hours():
    data = request.json
    room_id = data.get('room_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not room_id or not start_time or not end_time:
        return jsonify({'error': 'Champs horaires manquants'}), 400

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO acces_horaire (room_id, start_time, end_time) VALUES (?, ?, ?)',
        (room_id, start_time, end_time)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True)
