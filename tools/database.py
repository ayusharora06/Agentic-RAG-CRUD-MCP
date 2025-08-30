"""
Singleton Database Manager
"""
import sqlite3
from pathlib import Path
from config import DB_PATH

class DatabaseManager:
    """Singleton database manager"""
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database and create tables"""
        # Create db directory if it doesn't exist
        DB_PATH.parent.mkdir(exist_ok=True)
        
        # Create connection
        self._connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        
        # Create tables
        cursor = self._connection.cursor()
        
        # Person table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        
        # Bank accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts (
                accountId INTEGER PRIMARY KEY AUTOINCREMENT,
                personId INTEGER NOT NULL,
                bankName TEXT NOT NULL,
                balance REAL NOT NULL,
                FOREIGN KEY (personId) REFERENCES persons(id) ON DELETE CASCADE
            )
        """)
        
        self._connection.commit()
        print(f"✅ Database initialized: {DB_PATH}")
    
    def get_connection(self):
        """Get database connection"""
        if self._connection is None:
            self._initialize_db()
        return self._connection
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

# Create singleton instance
db_manager = DatabaseManager()

def get_db():
    """Get database connection for use in with statements"""
    return db_manager.get_connection()