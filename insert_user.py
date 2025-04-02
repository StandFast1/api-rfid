import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Exemple d'utilisateur admin avec badge UID
cursor.execute('''
INSERT INTO users (name, role, badgeuid)
VALUES (?, ?, ?)
''', ('Alice', 'admin', '539191D'))

conn.commit()
conn.close()

print("✅ Utilisateur inséré avec succès.")
