from app.database.mongodb import Database

# Export Database class
__all__ = ["Database"]

# Định nghĩa các event handlers cho kết nối đến database
async def connect_to_db():
    """Handler kết nối tới database khi ứng dụng khởi động."""
    await Database.connect_to_mongodb()

async def close_db_connection():
    """Handler đóng kết nối database khi ứng dụng shutdown."""
    await Database.close_mongodb_connection() 