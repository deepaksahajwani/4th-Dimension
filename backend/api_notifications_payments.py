"""
API Endpoints for In-App Notifications and Payment Tracking
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Database connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'architecture_firm')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Create router
notifications_payments_router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    link: Optional[str] = None
    project_id: Optional[str] = None
    read: bool
    created_at: str


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


class PaymentCreate(BaseModel):
    project_id: str
    amount: float
    payment_mode: str  # cash, cheque, online, bank_transfer
    payment_date: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    project_id: str
    client_id: str
    amount: float
    payment_mode: str
    payment_date: str
    status: str
    created_by_id: str
    created_at: str


# ============================================
# IN-APP NOTIFICATIONS ENDPOINTS
# ============================================

@notifications_payments_router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50
):
    """
    Get user's notifications
    
    Query params:
    - unread_only: If True, return only unread notifications
    - limit: Maximum number of notifications to return
    """
    try:
        query = {"user_id": user_id}
        if unread_only:
            query["read"] = False
        
        notifications = await db.notifications.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Convert datetime to string
        for notif in notifications:
            if isinstance(notif.get('created_at'), datetime):
                notif['created_at'] = notif['created_at'].isoformat()
        
        return notifications
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.get("/notifications/unread-count")
async def get_unread_count(user_id: str):
    """Get count of unread notifications"""
    try:
        count = await db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })
        
        return {"unread_count": count}
        
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.patch("/notifications/mark-read")
async def mark_notifications_read(request: MarkReadRequest):
    """Mark one or more notifications as read"""
    try:
        result = await db.notifications.update_many(
            {"id": {"$in": request.notification_ids}},
            {"$set": {"read": True}}
        )
        
        return {
            "success": True,
            "modified_count": result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error marking notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.patch("/notifications/{notification_id}/read")
async def mark_single_notification_read(notification_id: str):
    """Mark a single notification as read"""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id},
            {"$set": {"read": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    try:
        result = await db.notifications.delete_one({"id": notification_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PAYMENT TRACKING ENDPOINTS
# ============================================

@notifications_payments_router.post("/payments/client-paid", response_model=PaymentResponse)
async def client_marks_payment(payment_data: PaymentCreate, client_id: str):
    """
    Client marks a payment as paid (for future client dashboard)
    Triggers notification to owner
    """
    try:
        from uuid import uuid4
        
        payment = {
            "id": str(uuid4()),
            "project_id": payment_data.project_id,
            "client_id": client_id,
            "amount": payment_data.amount,
            "payment_mode": payment_data.payment_mode,
            "payment_date": payment_data.payment_date or datetime.now(timezone.utc).isoformat(),
            "notes": payment_data.notes,
            "status": "pending_verification",  # Owner needs to verify
            "created_by_id": client_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payments.insert_one(payment)
        
        # Trigger notification to owner
        try:
            from notification_triggers_v2 import notify_fees_paid_by_client
            await notify_fees_paid_by_client(
                project_id=payment_data.project_id,
                amount=payment_data.amount,
                payment_mode=payment_data.payment_mode,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error sending payment notification: {str(e)}")
        
        return payment
        
    except Exception as e:
        logger.error(f"Error recording client payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.post("/payments/owner-received", response_model=PaymentResponse)
async def owner_confirms_payment(payment_data: PaymentCreate, owner_id: str):
    """
    Owner records fees received
    Triggers notification to client (WhatsApp for cash, Email with invoice for cheque/online)
    """
    try:
        from uuid import uuid4
        
        # Get project to find client
        project = await db.projects.find_one({"id": payment_data.project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        client_id = project.get('client_id')
        
        payment = {
            "id": str(uuid4()),
            "project_id": payment_data.project_id,
            "client_id": client_id,
            "amount": payment_data.amount,
            "payment_mode": payment_data.payment_mode,
            "payment_date": payment_data.payment_date or datetime.now(timezone.utc).isoformat(),
            "notes": payment_data.notes,
            "status": "received",
            "invoice_generated": False,  # Will be True when invoice module is built
            "invoice_url": None,
            "created_by_id": owner_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payments.insert_one(payment)
        
        # Trigger notification to client
        try:
            from notification_triggers_v2 import notify_fees_received_by_owner
            await notify_fees_received_by_owner(
                project_id=payment_data.project_id,
                amount=payment_data.amount,
                payment_mode=payment_data.payment_mode,
                client_id=client_id,
                invoice_url=None  # Will be generated by document system later
            )
        except Exception as e:
            logger.error(f"Error sending payment confirmation notification: {str(e)}")
        
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording owner payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.get("/payments/project/{project_id}")
async def get_project_payments(project_id: str):
    """Get all payments for a project"""
    try:
        payments = await db.payments.find(
            {"project_id": project_id},
            {"_id": 0}
        ).sort("payment_date", -1).to_list(100)
        
        # Calculate totals
        total_received = sum(p['amount'] for p in payments if p['status'] == 'received')
        total_pending = sum(p['amount'] for p in payments if p['status'] == 'pending_verification')
        
        return {
            "payments": payments,
            "total_received": total_received,
            "total_pending": total_pending
        }
        
    except Exception as e:
        logger.error(f"Error fetching project payments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.get("/payments/client/{client_id}")
async def get_client_payments(client_id: str):
    """Get all payments for a client across all projects"""
    try:
        payments = await db.payments.find(
            {"client_id": client_id},
            {"_id": 0}
        ).sort("payment_date", -1).to_list(100)
        
        return {"payments": payments}
        
    except Exception as e:
        logger.error(f"Error fetching client payments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@notifications_payments_router.patch("/payments/{payment_id}/verify")
async def verify_payment(payment_id: str):
    """Owner verifies a client-submitted payment"""
    try:
        result = await db.payments.update_one(
            {"id": payment_id},
            {"$set": {
                "status": "received",
                "verified_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {"success": True, "message": "Payment verified"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
