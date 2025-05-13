#!/usr/bin/env python3
import requests
import json
import sys
import os
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

# Mặc định URL API
DEFAULT_API_URL = "http://localhost:8000"

def send_notification(customer_id, content, notification_type="custom", api_url=None):
    """
    Gửi thông báo đến service thông báo.
    
    Args:
        customer_id: ID của khách hàng
        content: Nội dung thông báo
        notification_type: Loại thông báo (mặc định: custom)
        api_url: URL của API (mặc định: sử dụng DEFAULT_API_URL)
    
    Returns:
        Response object từ requests
    """
    if api_url is None:
        api_url = os.getenv("API_URL", DEFAULT_API_URL)
    
    url = f"{api_url}/notifications"
    
    payload = {
        "type": notification_type,
        "customer_id": customer_id,
        "content": content
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi thông báo: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Sử dụng: python trigger_notification.py <customer_id> <notification_content> [notification_type]")
        sys.exit(1)
    
    customer_id = sys.argv[1]
    content = sys.argv[2]
    notification_type = sys.argv[3] if len(sys.argv) > 3 else "custom"
    
    result = send_notification(customer_id, content, notification_type)
    
    if result:
        print(f"Đã gửi thông báo thành công: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print("Không thể gửi thông báo.") 