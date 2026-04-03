from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from store import get_transactions, add_transaction, update_transaction, delete_transaction, clear_transactions
from datetime import datetime

router = APIRouter()

class TransactionCreate(BaseModel):
    date: str
    description: str
    amount: float
    type: str
    category: str

class TransactionUpdate(BaseModel):
    date: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None

@router.get("/")
def get_all_transactions(
    type: Optional[str] = None,
    category: Optional[str] = None,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    search: Optional[str] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 10000
):
    try:
        txns = list(get_transactions())  # Copy to avoid mutating shared in-memory list
        if type:
            txns = [t for t in txns if t['type'] == type]
        if category:
            txns = [t for t in txns if t['category'] == category]
        if from_date:
            txns = [t for t in txns if t.get('date', '') >= from_date]
        if to_date:
            txns = [t for t in txns if t.get('date', '') <= to_date]
        if search:
            s = search.lower()
            txns = [t for t in txns if s in t.get('description', '').lower()]

        txns.sort(key=lambda x: x.get('date', ''), reverse=True)
        total = len(txns)

        p = page or 1
        l = limit or 10000
        txns = txns[(p - 1) * l : p * l]

        return {"success": True, "data": txns, "total": total, "page": p}
    except Exception as e:
        import traceback
        return {"success": False, "message": "Failed to fetch transactions", "error": str(e), "trace": traceback.format_exc()}

@router.post("/")
def create_transaction(item: TransactionCreate):
    try:
        if item.type not in ["income", "expense"]:
            return {"success": False, "message": "type must be income or expense"}
        if item.amount < 0:
            return {"success": False, "message": "amount must be a positive number"}

        txn = add_transaction(item.model_dump())
        return {"success": True, "data": txn}
    except Exception as e:
        return {"success": False, "message": "Failed to add transaction", "error": str(e)}

@router.put("/{id}")
def edit_transaction(id: str, item: TransactionUpdate):
    try:
        updates = {k: v for k, v in item.model_dump().items() if v is not None}
        updated = update_transaction(id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"success": True, "data": updated}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        return {"success": False, "message": "Failed to update transaction", "error": str(e)}

@router.delete("/all")
def clear_all():
    """Clear all transactions endpoint"""
    try:
        clear_transactions()
        return {"success": True, "message": "All transactions deleted"}
    except Exception as e:
        return {"success": False, "message": "Failed to clear transactions", "error": str(e)}

@router.delete("/{id}")
def remove_transaction(id: str):
    try:
        deleted = delete_transaction(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"success": True, "message": "Deleted"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        return {"success": False, "message": "Failed to delete transaction", "error": str(e)}
