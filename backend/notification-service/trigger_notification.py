import requests
import sys
import json

def trigger_notification(customer_id, content):
    url = "http://localhost:8000/notifications"
    
    payload = {
        "type": "test",
        "customer_id": customer_id,
        "content": content
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception if request failed
        print("Notification sent successfully:")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python trigger_notification.py <customer_id> <notification_message>")
        sys.exit(1)
    
    customer_id = sys.argv[1]
    message = sys.argv[2]
    
    trigger_notification(customer_id, message) 