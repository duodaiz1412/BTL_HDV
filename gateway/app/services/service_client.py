import httpx
from fastapi import HTTPException

async def call_service(url, method="GET", data=None, params=None, timeout=10.0, error_message="Service error"):
    """
    Hàm tiện ích để gọi đến các service khác
    
    Args:
        url: URL đến service cần gọi
        method: Phương thức HTTP (GET, POST, PUT, DELETE)
        data: Dữ liệu gửi đi (cho POST, PUT)
        params: Query parameters
        timeout: Thời gian chờ tối đa (giây)
        error_message: Thông báo lỗi mặc định
    
    Returns:
        Response data từ service
    
    Raises:
        HTTPException: Nếu có lỗi khi gọi service
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, json=data, params=params)
            elif method == "PUT":
                response = await client.put(url, json=data, params=params)
            elif method == "DELETE":
                response = await client.delete(url, params=params)
            else:
                raise ValueError(f"Phương thức HTTP không hỗ trợ: {method}")
            
            # Xử lý lỗi HTTP
            if response.status_code >= 400:
                detail = f"{error_message}: {response.text}"
                raise HTTPException(status_code=response.status_code, detail=detail)
            
            # Trả về kết quả
            return response.json()
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail=f"Kết nối đến service quá hạn: {url}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Lỗi kết nối đến service {url}: {str(e)}")
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) 