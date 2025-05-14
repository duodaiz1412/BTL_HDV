from fastapi import APIRouter, HTTPException
from typing import Dict
from app.models import CustomerBase, CustomerCreate, CustomerResponse, CustomerLogin, CustomerUpdate
from app.database import (
    get_customer_by_id,
    get_customer_by_email,
    create_customer,
    update_customer,
    delete_customer
)
from app.services import verify_password, get_password_hash
import logging

logger = logging.getLogger("customer-service")

router = APIRouter(prefix="/customers", tags=["customers"])

@router.post("", response_model=CustomerResponse)
async def create_customer_endpoint(customer: CustomerCreate):
    try:
        # Kiểm tra xem email đã tồn tại chưa
        existing_customer = await get_customer_by_email(customer.email)
        if existing_customer:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Tạo customer mới
        customer_dict = customer.dict()
        customer_dict["password"] = get_password_hash(customer.password)
        
        result = await create_customer(customer_dict)
        return result
    except HTTPException:
        # Tiếp tục ném lại HTTP exception 
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Dict[str, str])
async def login_endpoint(customer: CustomerLogin):
    try:
        customer_doc = await get_customer_by_email(customer.email)
        
        if not customer_doc or not verify_password(customer.password, customer_doc["password"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        return {
            "message": "Login successful", 
            "customer_id": str(customer_doc["_id"])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer_endpoint(customer_id: str):
    try:
        customer = await get_customer_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving customer: {e}")
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

@router.put("/{customer_id}", response_model=Dict[str, str])
async def update_customer_endpoint(customer_id: str, customer: CustomerUpdate):
    try:
        success = await update_customer(customer_id, customer.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

@router.delete("/{customer_id}", response_model=Dict[str, str])
async def delete_customer_endpoint(customer_id: str):
    try:
        success = await delete_customer(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=400, detail="Invalid customer ID format") 