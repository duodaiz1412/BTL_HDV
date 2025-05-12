from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Customer Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.customer_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class CustomerBase(BaseModel):
    email: EmailStr
    name: str
    phone: str

class CustomerCreate(CustomerBase):
    password: str

class Customer(CustomerBase):
    id: str
    created_at: datetime

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def convert_mongo_id(customer):
    if customer:
        customer["id"] = str(customer["_id"])
        del customer["_id"]
    return customer

# Routes
@app.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    # Check if email already exists
    if await db.customers.find_one({"email": customer.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create customer
    customer_dict = customer.dict()
    customer_dict["password"] = get_password_hash(customer.password)
    customer_dict["created_at"] = datetime.now()
    
    result = await db.customers.insert_one(customer_dict)
    customer_dict["id"] = str(result.inserted_id)
    del customer_dict["_id"]
    
    return customer_dict

@app.post("/customers/login")
async def login(customer: dict):
    email = customer.get("email")
    password = customer.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )
    
    customer_doc = await db.customers.find_one({"email": email})
    if not customer_doc or not verify_password(password, customer_doc["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    return {"message": "Login successful", "customer_id": str(customer_doc["_id"])}

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    try:
        customer = await db.customers.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        return convert_mongo_id(customer)
    except:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

@app.put("/customers/{customer_id}")
async def update_customer(customer_id: str, customer: CustomerBase):
    try:
        result = await db.customers.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": customer.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid customer ID format")

@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    try:
        result = await db.customers.delete_one({"_id": ObjectId(customer_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid customer ID format") 