import json
import sqlite3
from typing import Annotated
from pathlib import Path

from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
import dspy

from database import setup_database
from agent import create_agent
from tools import upload_image, analyze_clothing_image, save_user_request

app = FastAPI(title="Outfit Assistant AI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


# --- Pydantic Models ---
class ClothingItemResponse(BaseModel):
    id: int
    image_path: str
    name: str | None
    tags: dict[str, list[str]]
    created_at: str


class OutfitRequest(BaseModel):
    occasion: str
    preferences: str = ""


class OutfitResponse(BaseModel):
    recommendation: str
    items: list[ClothingItemResponse]


class SaveOutfitRequest(BaseModel):
    name: str
    clothing_ids: list[int]
    occasion: str = ""


# --- Dependency Functions ---
def get_db_connection():
    """Get database connection with proper cleanup."""
    conn = setup_database()
    try:
        yield conn
    finally:
        conn.close()


def get_agent(conn: Annotated[sqlite3.Connection, Depends(get_db_connection)]) -> dspy.Module:
    """Get the outfit assistant agent."""
    return create_agent(conn)


# --- HTML Routes ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/wardrobe", response_class=HTMLResponse)
async def wardrobe_page(request: Request):
    """Render the wardrobe page."""
    return templates.TemplateResponse("wardrobe.html", {"request": request})


@app.get("/outfits", response_class=HTMLResponse)
async def outfits_page(request: Request):
    """Render the saved outfits page."""
    return templates.TemplateResponse("outfits.html", {"request": request})


# --- API Endpoints ---
@app.post("/api/clothes/upload")
async def upload_clothing_image(
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a clothing image.
    Returns the file path and suggested tags from AI analysis.
    """
    try:
        # Read file data
        file_data = await file.read()
        
        # Upload image
        file_path = upload_image(file_data, file.filename)
        
        if file_path.startswith("Error"):
            raise HTTPException(status_code=400, detail=file_path)
        
        # Analyze image with AI
        analysis_result = analyze_clothing_image(file_path)
        
        try:
            # Parse JSON response
            tags = json.loads(analysis_result)
        except json.JSONDecodeError:
            # If analysis fails, return with empty tags
            tags = {
                "type": [],
                "color": [],
                "category": [],
                "occasion": [],
                "style": []
            }
        
        return {
            "success": True,
            "file_path": file_path,
            "suggested_tags": tags
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clothes")
async def save_clothing(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    image_path: str = Form(...),
    name: str = Form(...),
    tags: str = Form(...),  # JSON string
) -> dict:
    """
    Save a clothing item with its tags to the database.
    """
    try:
        # Parse tags JSON
        print(f"[API] Received tags: {tags}")
        tags_dict = json.loads(tags)
        print(f"[API] Parsed tags_dict: {tags_dict}")
        
        # Import save function
        from tools import save_clothing_item
        
        # Save to database
        result = save_clothing_item(conn, image_path, name, tags_dict)
        print(f"[API] Save result: {result}")
        
        if result.startswith("Error"):
            raise HTTPException(status_code=400, detail=result)
        
        return {"success": True, "message": result}
    
    except json.JSONDecodeError as e:
        print(f"[API ERROR] JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")
    except Exception as e:
        print(f"[API ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes")
async def get_all_clothes(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> list[ClothingItemResponse]:
    """
    Get all clothing items from the wardrobe.
    """
    try:
        from tools import get_all_clothes as get_clothes_tool
        
        result = get_clothes_tool(conn)
        print(f"[API] get_all_clothes result: {result}")
        
        # Parse string result to list
        import ast
        clothes_list = ast.literal_eval(result)
        print(f"[API] Parsed clothes_list: {clothes_list}")
        
        return [ClothingItemResponse(**item) for item in clothes_list]
    
    except Exception as e:
        print(f"[API ERROR] get_all_clothes exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes/{clothing_id}")
async def get_clothing_detail(
    clothing_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> ClothingItemResponse:
    """
    Get details of a specific clothing item.
    """
    try:
        cursor = conn.cursor()
        
        # Get clothing item
        cursor.execute("""
            SELECT id, image_path, name, created_at
            FROM clothes
            WHERE id = ?
        """, (clothing_id,))
        
        cloth = cursor.fetchone()
        
        if not cloth:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
        # Get tags
        cursor.execute("""
            SELECT tag_type, tag_value
            FROM tags
            WHERE clothing_id = ?
        """, (clothing_id,))
        
        tags = cursor.fetchall()
        tags_dict = {}
        for tag_type, tag_value in tags:
            if tag_type not in tags_dict:
                tags_dict[tag_type] = []
            tags_dict[tag_type].append(tag_value)
        
        return ClothingItemResponse(
            id=cloth[0],
            image_path=cloth[1],
            name=cloth[2],
            tags=tags_dict,
            created_at=cloth[3]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/clothes/{clothing_id}")
async def delete_clothing(
    clothing_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> dict:
    """
    Delete a clothing item.
    """
    try:
        cursor = conn.cursor()
        
        # Get image path for deletion
        cursor.execute("SELECT image_path FROM clothes WHERE id = ?", (clothing_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
        image_path = result[0]
        
        # Delete from database (tags will be cascade deleted)
        cursor.execute("DELETE FROM clothes WHERE id = ?", (clothing_id,))
        conn.commit()
        
        # Delete image file
        try:
            Path(image_path).unlink()
        except:
            pass  # Ignore if file doesn't exist
        
        return {"success": True, "message": "Clothing item deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits/generate")
async def generate_outfit(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    agent: Annotated[dspy.Module, Depends(get_agent)],
    request: OutfitRequest,
) -> dict:
    """
    Generate an outfit recommendation based on occasion and preferences.
    """
    try:
        # Get wardrobe context
        from tools import get_all_clothes as get_clothes_tool
        wardrobe_context = get_clothes_tool(conn)
        
        # Create query for agent
        query = f"Create an outfit recommendation for {request.occasion}"
        if request.preferences:
            query += f" with preferences: {request.preferences}"
        
        # Call agent
        result = agent(question=query, wardrobe_context=wardrobe_context)
        
        # Save request to database
        save_user_request(conn, query, result.answer)
        
        return {
            "success": True,
            "recommendation": result.answer
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits")
async def save_outfit(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    request: SaveOutfitRequest,
) -> dict:
    """
    Save an outfit combination.
    """
    try:
        from tools import save_outfit as save_outfit_tool
        
        result = save_outfit_tool(
            conn,
            request.name,
            request.clothing_ids,
            request.occasion
        )
        
        if result.startswith("Error"):
            raise HTTPException(status_code=400, detail=result)
        
        return {"success": True, "message": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits")
async def get_saved_outfits(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> list[dict]:
    """
    Get all saved outfits.
    """
    try:
        from tools import get_saved_outfits as get_outfits_tool
        
        result = get_outfits_tool(conn)
        print(f"[API] get_saved_outfits result: {result}")
        
        # Parse string result to list
        import ast
        outfits_list = ast.literal_eval(result)
        
        return outfits_list
    
    except Exception as e:
        print(f"[API ERROR] get_saved_outfits exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits/{outfit_id}")
async def get_outfit_detail(
    outfit_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> dict:
    """
    Get details of a specific saved outfit.
    """
    try:
        cursor = conn.cursor()
        
        # Get outfit
        cursor.execute("""
            SELECT id, name, occasion, created_at
            FROM outfits
            WHERE id = ?
        """, (outfit_id,))
        
        outfit = cursor.fetchone()
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
        # Get outfit items
        cursor.execute("""
            SELECT c.id, c.image_path, c.name, oi.item_order
            FROM clothes c
            JOIN outfit_items oi ON c.id = oi.clothing_id
            WHERE oi.outfit_id = ?
            ORDER BY oi.item_order
        """, (outfit_id,))
        
        items = cursor.fetchall()
        
        return {
            "id": outfit[0],
            "name": outfit[1],
            "occasion": outfit[2],
            "created_at": outfit[3],
            "items": [
                {
                    "id": item[0],
                    "image_path": item[1],
                    "name": item[2],
                    "order": item[3]
                }
                for item in items
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
