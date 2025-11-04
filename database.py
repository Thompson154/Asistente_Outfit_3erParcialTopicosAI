import sqlite3
from datetime import datetime


def setup_database() -> sqlite3.Connection:
    # check_same_thread=False required for FastAPI multi-threading
    conn = sqlite3.connect("outfit_assistant.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clothing_id INTEGER NOT NULL,
            tag_type TEXT NOT NULL,
            tag_value TEXT NOT NULL,
            FOREIGN KEY (clothing_id) REFERENCES clothes(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_clothing ON tags(clothing_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_type_value ON tags(tag_type, tag_value);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            occasion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfit_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outfit_id INTEGER NOT NULL,
            clothing_id INTEGER NOT NULL,
            item_order INTEGER NOT NULL,
            FOREIGN KEY (outfit_id) REFERENCES outfits(id) ON DELETE CASCADE,
            FOREIGN KEY (clothing_id) REFERENCES clothes(id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print("Outfit Assistant database initialized")
    return conn
