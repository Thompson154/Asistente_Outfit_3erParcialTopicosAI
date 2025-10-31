import sqlite3
from datetime import datetime


def setup_database() -> sqlite3.Connection:
    """
    Creates a SQLite database for the Outfit Assistant with tables:
    - clothes: stores clothing items and their images
    - tags: stores tags associated with each clothing item
    - outfits: stores saved outfit combinations
    - outfit_items: links clothing items to outfits
    - user_requests: stores user queries and AI responses
    """
    conn = sqlite3.connect("outfit_assistant.db")
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    # --- Table 1: Clothes ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clothes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Table 2: Tags ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clothing_id INTEGER NOT NULL,
            tag_type TEXT NOT NULL,
            tag_value TEXT NOT NULL,
            FOREIGN KEY (clothing_id) REFERENCES clothes(id) ON DELETE CASCADE
        );
    """)

    # Create index for faster tag queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_clothing 
        ON tags(clothing_id);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tags_type_value 
        ON tags(tag_type, tag_value);
    """)

    # --- Table 3: Outfits ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            occasion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # --- Table 4: Outfit Items ---
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

    # --- Table 5: User Requests ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print("[Database] Outfit Assistant database initialized successfully.")
    return conn
