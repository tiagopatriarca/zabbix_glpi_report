import sqlite3
import hashlib
import os

DB_PATH = "data/database.db"

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_clients (
            user_id INTEGER,
            client_id INTEGER,
            PRIMARY KEY (user_id, client_id),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS zabbix_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS glpi_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            user_token TEXT NOT NULL,
            app_token TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        )
    ''')
    
    # Create default admin if not exists
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        pwd_hash = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", ("admin", pwd_hash, 1))
        
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    conn = get_db()
    c = conn.cursor()
    pwd_hash = hash_password(password)
    c.execute("SELECT id, username, is_admin FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_clients_for_user(user_id, is_admin):
    conn = get_db()
    c = conn.cursor()
    if is_admin:
        c.execute("SELECT id, name FROM clients ORDER BY name")
    else:
        c.execute('''
            SELECT c.id, c.name FROM clients c
            JOIN user_clients uc ON c.id = uc.client_id
            WHERE uc.user_id = ? ORDER BY c.name
        ''', (user_id,))
    clients = [dict(row) for row in c.fetchall()]
    conn.close()
    return clients

def get_zabbix_configs(client_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM zabbix_configs WHERE client_id = ?", (client_id,))
    configs = [dict(row) for row in c.fetchall()]
    conn.close()
    return configs

def get_glpi_configs(client_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM glpi_configs WHERE client_id = ?", (client_id,))
    configs = [dict(row) for row in c.fetchall()]
    conn.close()
    return configs

def update_client(client_id, name):
    conn = get_db()
    conn.execute("UPDATE clients SET name = ? WHERE id = ?", (name, client_id))
    conn.commit()
    conn.close()

def update_zabbix_config(config_id, name, url, username, password):
    conn = get_db()
    conn.execute("UPDATE zabbix_configs SET name = ?, url = ?, username = ?, password = ? WHERE id = ?", 
                 (name, url, username, password, config_id))
    conn.commit()
    conn.close()

def update_glpi_config(config_id, name, url, user_token, app_token):
    conn = get_db()
    conn.execute("UPDATE glpi_configs SET name = ?, url = ?, user_token = ?, app_token = ? WHERE id = ?", 
                 (name, url, user_token, app_token, config_id))
    conn.commit()
    conn.close()

def update_user(user_id, username, password, is_admin):
    conn = get_db()
    if password:
        pwd_hash = hash_password(password)
        conn.execute("UPDATE users SET username = ?, password_hash = ?, is_admin = ? WHERE id = ?", 
                     (username, pwd_hash, is_admin, user_id))
    else:
        conn.execute("UPDATE users SET username = ?, is_admin = ? WHERE id = ?", 
                     (username, is_admin, user_id))
    conn.commit()
    conn.close()
