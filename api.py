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

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Singleton pattern: Initialize DSPy and agent once at startup
_agent_instance = None
_agent_conn = None

@app.on_event("startup")
async def startup_event():
    global _agent_instance, _agent_conn
    print("Initializing Outfit Assistant Agent...")
    _agent_conn = setup_database()
    _agent_instance = create_agent(_agent_conn)
    print("Agent initialized successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    global _agent_conn
    if _agent_conn:
        _agent_conn.close()
        print("Agent connection closed.")


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


def get_db_connection():
    conn = setup_database()
    try:
        yield conn
    finally:
        conn.close()


def get_agent() -> dspy.Module:
    global _agent_instance
    if _agent_instance is None:
        raise RuntimeError("Agent not initialized. Make sure the application has started.")
    return _agent_instance


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/wardrobe", response_class=HTMLResponse)
async def wardrobe_page(request: Request):
    return templates.TemplateResponse("wardrobe.html", {"request": request})


@app.get("/outfits", response_class=HTMLResponse)
async def outfits_page(request: Request):
    return templates.TemplateResponse("outfits.html", {"request": request})
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


@app.post("/api/clothes/upload")
async def upload_clothing_image(file: UploadFile = File(...)) -> dict:
    try:
        file_data = await file.read()
        file_path = upload_image(file_data, file.filename)
        
        if file_path.startswith("Error"):
            raise HTTPException(status_code=400, detail=file_path)
        
        analysis_result = analyze_clothing_image(file_path)
        
        try:
            tags = json.loads(analysis_result)
        except json.JSONDecodeError:
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
    tags: str = Form(...),
) -> dict:
    try:
        tags_dict = json.loads(tags)
        from tools import save_clothing_item
        result = save_clothing_item(conn, image_path, name, tags_dict)
        
        if result.startswith("Error"):
            raise HTTPException(status_code=400, detail=result)
        
        return {"success": True, "message": result}
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes")
async def get_all_clothes(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> list[ClothingItemResponse]:
    try:
        from tools import get_all_clothes as get_clothes_tool
        result = get_clothes_tool(conn)
        import ast
        clothes_list = ast.literal_eval(result)
        return [ClothingItemResponse(**item) for item in clothes_list]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clothes/{clothing_id}")
async def get_clothing_detail(
    clothing_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> ClothingItemResponse:
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image_path, name, created_at
            FROM clothes
            WHERE id = ?
        """, (clothing_id,))
        
        cloth = cursor.fetchone()
        
        if not cloth:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
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
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT image_path FROM clothes WHERE id = ?", (clothing_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        
        image_path = result[0]
        cursor.execute("DELETE FROM clothes WHERE id = ?", (clothing_id,))
        conn.commit()
        
        try:
            Path(image_path).unlink()
        except:
            pass
        
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
    try:
        from tools import get_all_clothes as get_clothes_tool
        wardrobe_context = get_clothes_tool(conn)
        
        query = f"Create an outfit recommendation for {request.occasion}"
        if request.preferences:
            query += f" with preferences: {request.preferences}"
        query += ". IMPORTANT: Include the specific clothing IDs in your response in the format: [ID:X] for each recommended item."
        
        result = agent(question=query, wardrobe_context=wardrobe_context)
        save_user_request(conn, query, result.answer)
        
        import re
        id_pattern = r'\[ID:(\d+)\]'
        clothing_ids = [int(match) for match in re.findall(id_pattern, result.answer)]
        
        cursor = conn.cursor()
        clothing_items = []
        
        type_order = {
            'jacket': 1, 'coat': 1, 'blazer': 1,
            'shirt': 2, 'blouse': 2, 't-shirt': 2, 'top': 2, 'sweater': 2,
            'pants': 3, 'jeans': 3, 'trousers': 3, 'skirt': 3, 'shorts': 3,
            'shoes': 4, 'sneakers': 4, 'boots': 4, 'heels': 4,
            'accessory': 5, 'hat': 5, 'scarf': 5, 'bag': 5
        }
        
        for clothing_id in clothing_ids:
            cursor.execute("""
                SELECT c.id, c.image_path, c.name, c.created_at
                FROM clothes c
                WHERE c.id = ?
            """, (clothing_id,))
            
            cloth = cursor.fetchone()
            if cloth:
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
                
                item_type = tags_dict.get('type', [''])[0].lower() if tags_dict.get('type') else ''
                order = type_order.get(item_type, 99)
                
                clothing_items.append({
                    "id": cloth[0],
                    "image_path": cloth[1],
                    "name": cloth[2],
                    "tags": tags_dict,
                    "created_at": cloth[3],
                    "order": order
                })
        
        clothing_items.sort(key=lambda x: x['order'])
        
        return {
            "success": True,
            "recommendation": result.answer,
            "clothing_items": clothing_items
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/outfits")
async def save_outfit(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
    request: SaveOutfitRequest,
) -> dict:
    try:
        from tools import save_outfit as save_outfit_tool
        result = save_outfit_tool(conn, request.name, request.clothing_ids, request.occasion)
        
        if result.startswith("Error"):
            raise HTTPException(status_code=400, detail=result)
        
        return {"success": True, "message": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits")
async def get_saved_outfits(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> list[dict]:
    try:
        from tools import get_saved_outfits as get_outfits_tool
        result = get_outfits_tool(conn)
        import ast
        outfits_list = ast.literal_eval(result)
        return outfits_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/outfits/{outfit_id}")
async def get_outfit_detail(
    outfit_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> dict:
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, occasion, created_at
            FROM outfits
            WHERE id = ?
        """, (outfit_id,))
        
        outfit = cursor.fetchone()
        
        if not outfit:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
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
