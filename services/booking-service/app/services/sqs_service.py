import json
import logging
import aioboto3
from datetime import datetime
from app.config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    BOOKING_CREATED_QUEUE_URL,
    PAYMENT_PROCESSED_QUEUE_URL,
    SEATS_BOOKED_QUEUE_URL
)

logger = logging.getLogger("booking-service")

# SQS Session global variable
sqs_session = None

# JSON Encoder tùy chỉnh để xử lý datetime
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def get_sqs_session():
    """Create and return a shared aioboto3 session."""
    global sqs_session
    if sqs_session is None:
        sqs_session = aioboto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    return sqs_session

async def send_sqs_message(queue_url, message):
    """Send a message to an SQS queue."""
    try:
        session = await get_sqs_session()
        async with session.client('sqs') as sqs_client:
            await sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message, cls=DateTimeEncoder)
            )
            logger.info(f"Message sent to SQS queue: {queue_url}")
            return True
    except Exception as e:
        logger.error(f"Error sending message to SQS: {e}")
        return False

async def send_booking_created_message(booking_data):
    """Send a message to the booking created queue."""
    return await send_sqs_message(BOOKING_CREATED_QUEUE_URL, booking_data)

async def send_seats_booked_message(booking_data):
    """Send a message to the seats booked queue."""
    return await send_sqs_message(SEATS_BOOKED_QUEUE_URL, booking_data)

def close_sqs_session():
    """Close the SQS session."""
    global sqs_session
    sqs_session = None 