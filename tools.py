import os
import sqlite3
import base64
from datetime import datetime
from pathlib import Path
from typing import Any
from PIL import Image
import openai
from dotenv import load_dotenv

load_dotenv()


def upload_image(image_data: bytes, filename: str) -> str:
    try:
        upload_dir = Path("uploads/clothes")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix
        unique_filename = f"cloth_{timestamp}{file_extension}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        try:
            img = Image.open(file_path)
            img.verify()
        except Exception as e:
            os.remove(file_path)
            return f"Error: Invalid image file - {str(e)}"
        
        return str(file_path)
    
    except Exception as e:
        return f"Error uploading image: {str(e)}"


def analyze_clothing_image(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this clothing item and provide tags in the following categories:
                            - type: (e.g., shirt, pants, dress, jacket, shoes, accessory)
                            - color: (primary colors visible)
                            - category: (e.g., casual, formal, sportswear, outerwear)
                            - occasion: (e.g., work, party, gym, everyday)
                            - style: (e.g., modern, vintage, elegant, sporty)
                            
                            Return ONLY a JSON object with this structure:
                            {
                                "type": ["shirt"],
                                "color": ["blue", "white"],
                                "category": ["casual"],
                                "occasion": ["everyday", "work"],
                                "style": ["modern"]
                            }
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean markdown code blocks
        if result.startswith("```json"):
            result = result[7:]
        elif result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        
        return result.strip()
    
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


def save_clothing_item(conn: sqlite3.Connection, image_path: str, name: str, tags_dict: dict[str, list[str]]) -> str:
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clothes (image_path, name) VALUES (?, ?)", (image_path, name))
        clothing_id = cursor.lastrowid
        
        for tag_type, tag_values in tags_dict.items():
            for tag_value in tag_values:
                cursor.execute(
                    "INSERT INTO tags (clothing_id, tag_type, tag_value) VALUES (?, ?, ?)",
                    (clothing_id, tag_type, tag_value)
                )
        
        conn.commit()
        return f"Success: Clothing item saved with ID {clothing_id}"
    
    except sqlite3.Error as e:
        return f"Error saving clothing item: {str(e)}"


def query_wardrobe(conn: sqlite3.Connection, filters: dict[str, Any] | None = None) -> str:
    try:
        cursor = conn.cursor()
        
        if filters:
            conditions = []
            params = []
            
            for tag_type, tag_value in filters.items():
                conditions.append("""
                    c.id IN (
                        SELECT clothing_id FROM tags 
                        WHERE tag_type = ? AND tag_value = ?
                    )
                """)
                params.extend([tag_type, tag_value])
            
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT DISTINCT c.id, c.image_path, c.name, c.created_at
                FROM clothes c
                WHERE {where_clause}
            """
            cursor.execute(query, params)
        else:
            cursor.execute("""
                SELECT id, image_path, name, created_at
                FROM clothes
                ORDER BY created_at DESC
            """)
        
        clothes = cursor.fetchall()
        result = []
        
        for cloth in clothes:
            cloth_id, image_path, name, created_at = cloth
            
            cursor.execute("""
                SELECT tag_type, tag_value
                FROM tags
                WHERE clothing_id = ?
            """, (cloth_id,))
            
            tags = cursor.fetchall()
            tags_dict = {}
            for tag_type, tag_value in tags:
                if tag_type not in tags_dict:
                    tags_dict[tag_type] = []
                tags_dict[tag_type].append(tag_value)
            
            result.append({
                "id": cloth_id,
                "image_path": image_path,
                "name": name,
                "tags": tags_dict,
                "created_at": created_at
            })
        
        return str(result)
    
    except sqlite3.Error as e:
        return f"Error querying wardrobe: {str(e)}"


def generate_outfit_recommendation(conn: sqlite3.Connection, occasion: str, preferences: str = "") -> str:
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT c.id, c.image_path, c.name
            FROM clothes c
            JOIN tags t ON c.id = t.clothing_id
            WHERE t.tag_type = 'occasion' AND t.tag_value LIKE ?
        """, (f"%{occasion}%",))
        
        occasion_matches = cursor.fetchall()
        
        if not occasion_matches:
            cursor.execute("SELECT id, image_path, name FROM clothes")
            occasion_matches = cursor.fetchall()
        
        result = []
        for cloth_id, image_path, name in occasion_matches:
            cursor.execute("""
                SELECT tag_type, tag_value
                FROM tags
                WHERE clothing_id = ?
            """, (cloth_id,))
            
            tags = cursor.fetchall()
            tags_dict = {}
            for tag_type, tag_value in tags:
                if tag_type not in tags_dict:
                    tags_dict[tag_type] = []
                tags_dict[tag_type].append(tag_value)
            
            result.append({
                "id": cloth_id,
                "image_path": image_path,
                "name": name,
                "tags": tags_dict
            })
        
        return str(result)
    
    except sqlite3.Error as e:
        return f"Error generating outfit: {str(e)}"


def save_outfit(conn: sqlite3.Connection, name: str, clothing_ids: list[int], occasion: str = "") -> str:
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO outfits (name, occasion) VALUES (?, ?)", (name, occasion))
        outfit_id = cursor.lastrowid
        
        for order, clothing_id in enumerate(clothing_ids, start=1):
            cursor.execute(
                "INSERT INTO outfit_items (outfit_id, clothing_id, item_order) VALUES (?, ?, ?)",
                (outfit_id, clothing_id, order)
            )
        
        conn.commit()
        return f"Success: Outfit '{name}' saved with ID {outfit_id}"
    
    except sqlite3.Error as e:
        return f"Error saving outfit: {str(e)}"


def get_all_clothes(conn: sqlite3.Connection) -> str:
    return query_wardrobe(conn, filters=None)


def get_saved_outfits(conn: sqlite3.Connection) -> str:
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, occasion, created_at
            FROM outfits
            ORDER BY created_at DESC
        """)
        
        outfits = cursor.fetchall()
        result = []
        
        for outfit_id, name, occasion, created_at in outfits:
            cursor.execute("""
                SELECT c.id, c.image_path, c.name, oi.item_order
                FROM clothes c
                JOIN outfit_items oi ON c.id = oi.clothing_id
                WHERE oi.outfit_id = ?
                ORDER BY oi.item_order
            """, (outfit_id,))
            
            items = cursor.fetchall()
            items_list = [
                {"id": item[0], "image_path": item[1], "name": item[2], "order": item[3]}
                for item in items
            ]
            
            result.append({
                "id": outfit_id,
                "name": name,
                "occasion": occasion,
                "items": items_list,
                "created_at": created_at
            })
        
        return str(result)
    
    except sqlite3.Error as e:
        return f"Error retrieving outfits: {str(e)}"


def save_user_request(conn: sqlite3.Connection, query: str, response: str) -> str:
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_requests (query, response) VALUES (?, ?)", (query, response))
        conn.commit()
        return "Success: Request saved"
    except sqlite3.Error as e:
        return f"Error saving request: {str(e)}"
