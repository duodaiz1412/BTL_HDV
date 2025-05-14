from app.main import app

# Chỉ để máy chủ uvicorn tìm thấy ứng dụng
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 