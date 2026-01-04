"""
Accounting Router - Financial Management
Refactored from server.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import Optional, List
import logging
import uuid

from utils.auth import get_current_user, require_owner, User
from utils.database import get_database
from models_projects import Accounting, AccountingCreate

db = get_database()
router = APIRouter(prefix="/accounting", tags=["Accounting"])
logger = logging.getLogger(__name__)


# ==================== BASIC ACCOUNTING ====================

@router.post("", response_model=Accounting)
async def create_accounting_entry(entry_data: AccountingCreate, current_user: User = Depends(require_owner)):
    """Create basic accounting entry"""
    entry = Accounting(
        transaction_type=entry_data.transaction_type,
        amount=entry_data.amount,
        project_id=entry_data.project_id,
        user_id=entry_data.user_id,
        description=entry_data.description,
        category=entry_data.category,
        created_by=current_user.id
    )
    
    entry_dict = entry.model_dump()
    entry_dict['date'] = entry_dict['date'].isoformat()
    
    await db.accounting.insert_one(entry_dict)
    return entry


@router.get("", response_model=List[Accounting])
async def get_accounting_entries(current_user: User = Depends(require_owner)):
    """Get all basic accounting entries"""
    entries = await db.accounting.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    for entry in entries:
        if isinstance(entry.get('date'), str):
            entry['date'] = datetime.fromisoformat(entry['date'])
    return entries


# ==================== PROJECT INCOME ====================

@router.get("/income")
async def get_all_project_income(current_user: User = Depends(get_current_user)):
    """Get income tracking for all projects (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        income_records = await db.project_income.find({}, {"_id": 0}).to_list(1000)
        
        for record in income_records:
            record['pending_amount'] = record.get('total_fee', 0) - record.get('received_amount', 0)
        
        return income_records
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project income error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/income/{project_id}")
async def get_project_income(project_id: str, current_user: User = Depends(get_current_user)):
    """Get income details for a specific project"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        income = await db.project_income.find_one({"project_id": project_id}, {"_id": 0})
        
        if not income:
            project = await db.projects.find_one({"id": project_id}, {"_id": 0, "title": 1})
            return {
                "project_id": project_id,
                "project_name": project.get('title') if project else None,
                "total_fee": 0,
                "received_amount": 0,
                "pending_amount": 0,
                "payments": []
            }
        
        income['pending_amount'] = income.get('total_fee', 0) - income.get('received_amount', 0)
        return income
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project income error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/income/{project_id}")
async def update_project_income(project_id: str, data: dict, current_user: User = Depends(get_current_user)):
    """Update income details for a project"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        project = await db.projects.find_one({"id": project_id}, {"_id": 0, "title": 1})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        existing = await db.project_income.find_one({"project_id": project_id})
        
        total_fee_str = data.get('total_fee', 0)
        total_fee = float(total_fee_str) if total_fee_str and total_fee_str != '' else 0.0
        
        if existing:
            received_amount = existing.get('received_amount', 0)
            record_id = existing.get('id')
        else:
            received_amount = 0
            record_id = str(uuid.uuid4())
        
        update_data = {
            "project_id": project_id,
            "project_name": project['title'],
            "total_fee": total_fee,
            "received_amount": received_amount,
            "pending_amount": total_fee - received_amount,
            "notes": data.get('notes'),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            await db.project_income.update_one(
                {"project_id": project_id},
                {"$set": {
                    "total_fee": total_fee,
                    "pending_amount": total_fee - received_amount,
                    "notes": update_data['notes'],
                    "updated_at": update_data['updated_at']
                }}
            )
        else:
            update_data["id"] = record_id
            update_data["payments"] = []
            update_data["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.project_income.insert_one(update_data)
        
        result = await db.project_income.find_one({"id": record_id}, {"_id": 0})
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update project income error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PAYMENTS ====================

@router.post("/income/{project_id}/payment")
async def add_payment(project_id: str, payment: dict, current_user: User = Depends(get_current_user)):
    """Add a payment entry to project income"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        payment_amount = float(payment['amount'])
        
        payment_entry = {
            "id": str(uuid.uuid4()),
            "amount": payment_amount,
            "payment_date": payment['payment_date'],
            "payment_mode": payment['payment_mode'],
            "bank_account": payment.get('bank_account'),
            "reference_number": payment.get('reference_number'),
            "notes": payment.get('notes'),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.project_income.update_one(
            {"project_id": project_id},
            {
                "$push": {"payments": payment_entry},
                "$inc": {"received_amount": payment_amount},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Income record not found")
        
        return {"success": True, "payment": payment_entry}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/income/{project_id}/payment/{payment_id}")
async def update_payment(project_id: str, payment_id: str, payment: dict, current_user: User = Depends(get_current_user)):
    """Update a payment entry"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        income_record = await db.project_income.find_one({"project_id": project_id})
        if not income_record:
            raise HTTPException(status_code=404, detail="Income record not found")
        
        payments = income_record.get('payments', [])
        payment_index = None
        old_amount = 0
        
        for i, p in enumerate(payments):
            if p.get('id') == payment_id:
                payment_index = i
                old_amount = p.get('amount', 0)
                break
        
        if payment_index is None:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        new_amount = float(payment['amount'])
        amount_difference = new_amount - old_amount
        
        updated_payment = {
            "id": payment_id,
            "amount": new_amount,
            "payment_date": payment['payment_date'],
            "payment_mode": payment['payment_mode'],
            "bank_account": payment.get('bank_account'),
            "reference_number": payment.get('reference_number'),
            "notes": payment.get('notes'),
            "created_at": payments[payment_index].get('created_at', datetime.now(timezone.utc).isoformat()),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.project_income.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    f"payments.{payment_index}": updated_payment,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"received_amount": amount_difference}
            }
        )
        
        return {"success": True, "payment": updated_payment}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/income/{project_id}/payment/{payment_id}")
async def delete_payment(project_id: str, payment_id: str, current_user: User = Depends(get_current_user)):
    """Delete a payment entry"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        income_record = await db.project_income.find_one({"project_id": project_id})
        if not income_record:
            raise HTTPException(status_code=404, detail="Income record not found")
        
        payments = income_record.get('payments', [])
        payment_to_delete = None
        
        for p in payments:
            if p.get('id') == payment_id:
                payment_to_delete = p
                break
        
        if not payment_to_delete:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment_amount = payment_to_delete.get('amount', 0)
        
        await db.project_income.update_one(
            {"project_id": project_id},
            {
                "$pull": {"payments": {"id": payment_id}},
                "$inc": {"received_amount": -payment_amount},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EXPENSE ACCOUNTS ====================

@router.get("/expense-accounts")
async def get_expense_accounts(current_user: User = Depends(get_current_user)):
    """Get all expense accounts (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        accounts = await db.expense_accounts.find({}, {"_id": 0}).to_list(1000)
        return accounts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get expense accounts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expense-accounts")
async def create_expense_account(account: dict, current_user: User = Depends(get_current_user)):
    """Create a new expense account"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        account_id = str(uuid.uuid4())
        account_data = {
            "id": account_id,
            "name": account['name'],
            "description": account.get('description'),
            "total_expenses": 0.0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.expense_accounts.insert_one(account_data)
        
        result = await db.expense_accounts.find_one({"id": account_id}, {"_id": 0})
        return {"success": True, "account": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create expense account error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expense-accounts/{account_id}")
async def update_expense_account(account_id: str, account: dict, current_user: User = Depends(get_current_user)):
    """Update an expense account"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        result = await db.expense_accounts.update_one(
            {"id": account_id},
            {"$set": {
                "name": account['name'],
                "description": account.get('description'),
                "is_active": account.get('is_active', True),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Expense account not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update expense account error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== EXPENSES ====================

@router.get("/expenses")
async def get_expenses(current_user: User = Depends(get_current_user), expense_account_id: Optional[str] = None):
    """Get all expenses (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        query = {}
        if expense_account_id:
            query["expense_account_id"] = expense_account_id
        
        expenses = await db.expenses.find(query, {"_id": 0}).sort("expense_date", -1).to_list(1000)
        return expenses
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get expenses error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expenses")
async def create_expense(expense: dict, current_user: User = Depends(get_current_user)):
    """Create a new expense entry"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        account = await db.expense_accounts.find_one(
            {"id": expense['expense_account_id']}, 
            {"_id": 0, "name": 1}
        )
        
        if not account:
            raise HTTPException(status_code=404, detail="Expense account not found")
        
        project_name = None
        if expense.get('project_id'):
            project = await db.projects.find_one(
                {"id": expense['project_id']}, 
                {"_id": 0, "title": 1}
            )
            project_name = project.get('title') if project else None
        
        expense_amount = float(expense['amount'])
        
        expense_data = {
            "id": str(uuid.uuid4()),
            "expense_account_id": expense['expense_account_id'],
            "expense_account_name": account['name'],
            "amount": expense_amount,
            "expense_date": expense['expense_date'],
            "description": expense['description'],
            "payment_mode": expense['payment_mode'],
            "bank_account": expense.get('bank_account'),
            "reference_number": expense.get('reference_number'),
            "vendor_name": expense.get('vendor_name'),
            "project_id": expense.get('project_id'),
            "project_name": project_name,
            "notes": expense.get('notes'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        expense_id = expense_data["id"]
        await db.expenses.insert_one(expense_data)
        
        await db.expense_accounts.update_one(
            {"id": expense['expense_account_id']},
            {
                "$inc": {"total_expenses": expense_amount},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        result = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
        return {"success": True, "expense": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create expense error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INCOME ACCOUNTS ====================

@router.get("/income-accounts")
async def get_income_accounts(current_user: User = Depends(get_current_user)):
    """Get all income accounts (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        accounts = await db.income_accounts.find({}, {"_id": 0}).to_list(1000)
        return accounts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get income accounts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/income-accounts")
async def create_income_account(account: dict, current_user: User = Depends(get_current_user)):
    """Create a new income account"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        account_id = str(uuid.uuid4())
        account_data = {
            "id": account_id,
            "name": account['name'],
            "description": account.get('description'),
            "total_income": 0.0,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.income_accounts.insert_one(account_data)
        
        result = await db.income_accounts.find_one({"id": account_id}, {"_id": 0})
        return {"success": True, "account": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create income account error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/income-accounts/{account_id}")
async def update_income_account(account_id: str, account: dict, current_user: User = Depends(get_current_user)):
    """Update an income account"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        result = await db.income_accounts.update_one(
            {"id": account_id},
            {"$set": {
                "name": account['name'],
                "description": account.get('description'),
                "is_active": account.get('is_active', True),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Income account not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update income account error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INCOME ENTRIES ====================

@router.get("/income-entries")
async def get_income_entries(current_user: User = Depends(get_current_user), income_account_id: Optional[str] = None):
    """Get all income entries (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        query = {}
        if income_account_id:
            query["income_account_id"] = income_account_id
        
        entries = await db.income_entries.find(query, {"_id": 0}).sort("income_date", -1).to_list(1000)
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get income entries error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/income-entries")
async def create_income_entry(income_entry: dict, current_user: User = Depends(get_current_user)):
    """Create a new income entry"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        account = await db.income_accounts.find_one(
            {"id": income_entry['income_account_id']}, 
            {"_id": 0, "name": 1}
        )
        
        if not account:
            raise HTTPException(status_code=404, detail="Income account not found")
        
        income_amount = float(income_entry['amount'])
        
        entry_data = {
            "id": str(uuid.uuid4()),
            "income_account_id": income_entry['income_account_id'],
            "income_account_name": account['name'],
            "amount": income_amount,
            "income_date": income_entry['income_date'],
            "description": income_entry['description'],
            "payment_mode": income_entry['payment_mode'],
            "bank_account": income_entry.get('bank_account'),
            "reference_number": income_entry.get('reference_number'),
            "source_name": income_entry.get('source_name'),
            "notes": income_entry.get('notes'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        entry_id = entry_data["id"]
        await db.income_entries.insert_one(entry_data)
        
        await db.income_accounts.update_one(
            {"id": income_entry['income_account_id']},
            {
                "$inc": {"total_income": income_amount},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        result = await db.income_entries.find_one({"id": entry_id}, {"_id": 0})
        return {"success": True, "income_entry": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create income entry error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SUMMARY ====================

@router.get("/summary")
async def get_accounting_summary(current_user: User = Depends(get_current_user)):
    """Get accounting summary (owner only)"""
    try:
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can access accounting")
        
        income_records = await db.project_income.find({}, {"_id": 0}).to_list(1000)
        total_fee = sum(r.get('total_fee', 0) for r in income_records)
        total_received = sum(r.get('received_amount', 0) for r in income_records)
        total_pending = total_fee - total_received
        
        income_accounts = await db.income_accounts.find({}, {"_id": 0}).to_list(1000)
        total_other_income = sum(a.get('total_income', 0) for a in income_accounts)
        
        expense_accounts = await db.expense_accounts.find({}, {"_id": 0}).to_list(1000)
        total_expenses = sum(a.get('total_expenses', 0) for a in expense_accounts)
        
        total_income = total_received + total_other_income
        
        return {
            "income": {
                "total_fee": total_fee,
                "received": total_received,
                "pending": total_pending,
                "other_income": total_other_income,
                "total": total_income
            },
            "expenses": {
                "total": total_expenses
            },
            "net": total_income - total_expenses
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get accounting summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
