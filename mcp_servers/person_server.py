"""
Person MCP Server using FastMCP
Provides CRUD operations for Person entities
"""
import sys
from pathlib import Path
# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP
from typing import Dict, List, Optional
from tools.database import get_db

# Initialize FastMCP server
mcp = FastMCP("person-mcp-server")

@mcp.tool()
async def create_person(name: str, age: int, email: str) -> Dict:
    """Create a new person in the database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO persons (name, age, email) VALUES (?, ?, ?)",
            (name, age, email)
        )
        conn.commit()
        person_id = cursor.lastrowid
        
        return {
            "success": True,
            "person": {
                "id": person_id,
                "name": name,
                "age": age,
                "email": email
            },
            "message": f"Person {name} created successfully with ID {person_id}"
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return {"success": False, "error": "Email already exists"}
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_person(person_id: int) -> Dict:
    """Get a person by ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "person": {
                    "id": row["id"],
                    "name": row["name"],
                    "age": row["age"],
                    "email": row["email"]
                }
            }
        return {"success": False, "error": "Person not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def list_persons() -> Dict:
    """List all persons in the database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM persons")
        rows = cursor.fetchall()
        
        persons = []
        for row in rows:
            persons.append({
                "id": row["id"],
                "name": row["name"],
                "age": row["age"],
                "email": row["email"]
            })
        
        return {
            "success": True,
            "persons": persons,
            "count": len(persons)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def search_person_by_name(name: str) -> Dict:
    """Search for a person by name"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM persons WHERE LOWER(name) = LOWER(?)", 
            (name,)
        )
        row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "person": {
                    "id": row["id"],
                    "name": row["name"],
                    "age": row["age"],
                    "email": row["email"]
                }
            }
        return {"success": False, "error": f"No person named {name} found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def update_person(
    person_id: int, 
    name: Optional[str] = None, 
    age: Optional[int] = None, 
    email: Optional[str] = None
) -> Dict:
    """Update a person's information"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current data
        cursor.execute("SELECT * FROM persons WHERE id = ?", (person_id,))
        current = cursor.fetchone()
        
        if not current:
            return {"success": False, "error": "Person not found"}
        
        # Use current values if not provided
        name = name or current["name"]
        age = age if age is not None else current["age"]
        email = email or current["email"]
        
        # Update
        cursor.execute(
            "UPDATE persons SET name = ?, age = ?, email = ? WHERE id = ?",
            (name, age, email, person_id)
        )
        conn.commit()
        
        return {
            "success": True,
            "person": {
                "id": person_id,
                "name": name,
                "age": age,
                "email": email
            },
            "message": f"Person {name} updated successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def delete_person(person_id: int) -> Dict:
    """Delete a person from the database"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if person exists
        cursor.execute("SELECT name FROM persons WHERE id = ?", (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return {"success": False, "error": "Person not found"}
        
        # Delete (bank accounts will cascade delete)
        cursor.execute("DELETE FROM persons WHERE id = ?", (person_id,))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Person {person['name']} deleted successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run as stdio server when called directly
    mcp.run(transport="stdio")