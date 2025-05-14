from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    email: EmailStr
    name: str
    phone: str

class CustomerCreate(CustomerBase):
    password: str

class CustomerResponse(CustomerBase):
    id: str
    created_at: datetime

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str

class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None 