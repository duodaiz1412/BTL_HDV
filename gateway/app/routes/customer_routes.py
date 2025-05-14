from fastapi import APIRouter, HTTPException
from app.services.service_client import call_service
from app.config.settings import CUSTOMER_SERVICE_URL

router = APIRouter(tags=["customers"])

@router.post("/auth/login")
async def login(customer: dict):
    """Đăng nhập người dùng"""
    try:
        return await call_service(
            f"{CUSTOMER_SERVICE_URL}/customers/login",
            method="POST",
            data={"email": customer.get("email"), "password": customer.get("password")},
            error_message="Lỗi xác thực"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đăng nhập: {str(e)}")

@router.post("/auth/register")
async def register(customer: dict):
    """Đăng ký người dùng mới"""
    return await call_service(
        f"{CUSTOMER_SERVICE_URL}/customers",
        method="POST",
        data=customer,
        error_message="Lỗi khi đăng ký"
    )

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Lấy thông tin chi tiết một khách hàng"""
    return await call_service(
        f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}",
        error_message="Error getting customer"
    )

@router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, customer: dict):
    """Cập nhật thông tin khách hàng"""
    return await call_service(
        f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}",
        method="PUT",
        data=customer,
        error_message="Error updating customer"
    ) 