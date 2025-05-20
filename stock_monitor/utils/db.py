import sqlite3
from datetime import datetime

DB_PATH = "data/stock_history.db"

def init_db():
    """Initialize the database and create the history table if it doesn't exist."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            data TEXT
        )
    """)
    connection.commit()
    connection.close()

def insert_history(symbol, data):
    """Insert stock operation history into the database."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO history (timestamp, symbol, data)
        VALUES (?, ?, ?)
    """, (datetime.now().isoformat(), symbol, data))
    connection.commit()
    connection.close()

def fetch_history():
    """Retrieve all history records."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM history")
    rows = cursor.fetchall()
    connection.close()
    return rows
