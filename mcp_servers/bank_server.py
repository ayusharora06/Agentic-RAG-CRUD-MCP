"""
Bank Account MCP Server using FastMCP
Provides CRUD operations for Bank Account entities
"""
import sys
from pathlib import Path
# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP
from typing import Dict, List, Optional
from tools.database import get_db

# Initialize FastMCP server
mcp = FastMCP("bank-mcp-server")

@mcp.tool()
async def create_bank_account(person_id: int, bank_name: str, balance: float) -> Dict:
    """Create a new bank account for a person"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if person exists
        cursor.execute("SELECT name FROM persons WHERE id = ?", (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return {"success": False, "error": f"Person with ID {person_id} not found"}
        
        cursor.execute(
            "INSERT INTO bank_accounts (personId, bankName, balance) VALUES (?, ?, ?)",
            (person_id, bank_name, balance)
        )
        conn.commit()
        account_id = cursor.lastrowid
        
        return {
            "success": True,
            "account": {
                "accountId": account_id,
                "personId": person_id,
                "bankName": bank_name,
                "balance": balance
            },
            "message": f"Bank account created successfully with ID {account_id} for {person['name']}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_bank_account(account_id: int) -> Dict:
    """Get a bank account by ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bank_accounts WHERE accountId = ?", (account_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "account": {
                    "accountId": row["accountId"],
                    "personId": row["personId"],
                    "bankName": row["bankName"],
                    "balance": row["balance"]
                }
            }
        return {"success": False, "error": "Bank account not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def list_bank_accounts() -> Dict:
    """List all bank accounts"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bank_accounts")
        rows = cursor.fetchall()
        
        accounts = []
        for row in rows:
            accounts.append({
                "accountId": row["accountId"],
                "personId": row["personId"],
                "bankName": row["bankName"],
                "balance": row["balance"]
            })
        
        return {
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_accounts_by_person(person_id: int) -> Dict:
    """Get all bank accounts for a specific person"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get person info
        cursor.execute("SELECT name FROM persons WHERE id = ?", (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return {"success": False, "error": f"Person with ID {person_id} not found"}
        
        # Get accounts
        cursor.execute("SELECT * FROM bank_accounts WHERE personId = ?", (person_id,))
        rows = cursor.fetchall()
        
        accounts = []
        total_balance = 0
        for row in rows:
            accounts.append({
                "accountId": row["accountId"],
                "bankName": row["bankName"],
                "balance": row["balance"]
            })
            total_balance += row["balance"]
        
        return {
            "success": True,
            "person": person["name"],
            "accounts": accounts,
            "total_balance": total_balance,
            "count": len(accounts)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def update_bank_account(
    account_id: int,
    bank_name: Optional[str] = None,
    balance: Optional[float] = None
) -> Dict:
    """Update a bank account's information"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current data
        cursor.execute("SELECT * FROM bank_accounts WHERE accountId = ?", (account_id,))
        current = cursor.fetchone()
        
        if not current:
            return {"success": False, "error": "Bank account not found"}
        
        # Use current values if not provided
        bank_name = bank_name or current["bankName"]
        balance = balance if balance is not None else current["balance"]
        
        # Update
        cursor.execute(
            "UPDATE bank_accounts SET bankName = ?, balance = ? WHERE accountId = ?",
            (bank_name, balance, account_id)
        )
        conn.commit()
        
        return {
            "success": True,
            "account": {
                "accountId": account_id,
                "personId": current["personId"],
                "bankName": bank_name,
                "balance": balance
            },
            "message": f"Bank account {account_id} updated successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def delete_bank_account(account_id: int) -> Dict:
    """Delete a bank account"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if account exists
        cursor.execute("SELECT * FROM bank_accounts WHERE accountId = ?", (account_id,))
        account = cursor.fetchone()
        
        if not account:
            return {"success": False, "error": "Bank account not found"}
        
        # Delete
        cursor.execute("DELETE FROM bank_accounts WHERE accountId = ?", (account_id,))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Bank account {account_id} deleted successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_person_with_accounts(person_id: int) -> Dict:
    """Get person details along with all their bank accounts (JOIN operation)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # JOIN query
        cursor.execute("""
            SELECT 
                p.id, p.name, p.age, p.email,
                b.accountId, b.bankName, b.balance
            FROM persons p
            LEFT JOIN bank_accounts b ON p.id = b.personId
            WHERE p.id = ?
        """, (person_id,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return {"success": False, "error": "Person not found"}
        
        # Build response
        first_row = rows[0]
        person_info = {
            "id": first_row["id"],
            "name": first_row["name"],
            "age": first_row["age"],
            "email": first_row["email"],
            "accounts": []
        }
        
        total_balance = 0
        for row in rows:
            if row["accountId"]:  # Account exists
                person_info["accounts"].append({
                    "accountId": row["accountId"],
                    "bankName": row["bankName"],
                    "balance": row["balance"]
                })
                total_balance += row["balance"]
        
        person_info["total_balance"] = total_balance
        
        return {
            "success": True,
            "data": person_info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Run as stdio server when called directly
    mcp.run(transport="stdio")