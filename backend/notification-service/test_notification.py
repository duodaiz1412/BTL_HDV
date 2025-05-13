import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def send_test_notification(customer_id, content, notification_type="test"):
    """
    Gửi thông báo test tới một khách hàng thông qua API
    
    Args:
        customer_id: ID của khách hàng
        content: Nội dung thông báo
        notification_type: Loại thông báo (mặc định: test)
        
    Returns:
        Response của API hoặc None nếu có lỗi
    """
    try:
        # Sử dụng API Gateway thay vì trực tiếp notification service
        api_url = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
        url = f"{api_url}/notifications"
        
        payload = {
            "customer_id": customer_id,
            "content": content,
            "type": notification_type,
            "status": "pending"
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print(f"Thông báo đã được gửi thành công:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi thông báo: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Server trả về: {e.response.status_code} - {e.response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Sử dụng: python test_notification.py <customer_id> <nội_dung_thông_báo> [loại_thông_báo]")
        sys.exit(1)
        
    customer_id = sys.argv[1]
    content = sys.argv[2]
    notification_type = sys.argv[3] if len(sys.argv) > 3 else "test"
    
    print(f"Gửi thông báo '{content}' đến khách hàng {customer_id}...")
    result = send_test_notification(customer_id, content, notification_type)
    
    if result:
        print("Thông báo đã được gửi thành công!")
    else:
        print("Gửi thông báo thất bại.") 