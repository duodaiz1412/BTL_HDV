import boto3
from botocore.exceptions import ClientError
import json
import os
from app.config.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

# AWS SQS client
sqs = boto3.client('sqs',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

async def send_sqs_message(queue_url, message):
    """
    Gửi tin nhắn đến hàng đợi SQS
    
    Args:
        queue_url (str): URL của hàng đợi SQS
        message (dict): Nội dung tin nhắn dạng dict
        
    Returns:
        dict or None: Kết quả từ API SQS hoặc None nếu lỗi
    """
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        return response
    except ClientError as e:
        print(f"Error sending message to SQS: {e}")
        return None 