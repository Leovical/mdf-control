import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mdf_control.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    conn = get_db_connection()
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM usuarios')
    resultado = cursor.fetchone()
    
    if resultado['total'] == 0:
        cursor.execute(
            'INSERT INTO usuarios (nome, email, cargo) VALUES (?, ?, ?)',
            ('Leonardo', 'leozim@gmail.com', 'Analista de TI')
        )
        
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()