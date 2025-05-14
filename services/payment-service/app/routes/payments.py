from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List
from app.models.models import PaymentBase
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("", response_model=Dict[str, Any])
async def create_payment(payment: PaymentBase, background_tasks: BackgroundTasks):
    """Tạo một payment mới."""
    try:
        payment_data = payment.dict()
        result = await PaymentService.create_payment(payment_data, background_tasks)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{payment_id}", response_model=Dict[str, Any])
async def get_payment(payment_id: str):
    """Lấy payment theo ID."""
    try:
        payment = await PaymentService.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@router.get("/booking/{booking_id}", response_model=List[Dict[str, Any]])
async def get_booking_payments(booking_id: str):
    """Lấy danh sách payment theo booking_id."""
    try:
        payments = await PaymentService.get_booking_payments(booking_id)
        return payments
    except Exception as e:
        return []

@router.put("/{payment_id}/status", response_model=Dict[str, str])
async def update_payment_status(payment_id: str, status: str, background_tasks: BackgroundTasks):
    """Cập nhật trạng thái của payment."""
    try:
        success = await PaymentService.update_payment_status(payment_id, status, background_tasks)
        if not success:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {"message": "Payment status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@router.post("/{payment_id}/refund", response_model=Dict[str, Any])
async def refund_payment(payment_id: str, background_tasks: BackgroundTasks):
    """Hoàn tiền cho payment."""
    try:
        result = await PaymentService.refund_payment(payment_id, background_tasks)
        if not result:
            raise HTTPException(status_code=404, detail="Payment not found")
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 