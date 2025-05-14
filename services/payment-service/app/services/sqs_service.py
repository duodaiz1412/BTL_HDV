import os
import aioboto3
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("payment-service")

class SQSService:
    session = None

    @classmethod
    async def get_session(cls):
        """Tạo và trả về phiên aioboto3 được chia sẻ."""
        if cls.session is None:
            cls.session = aioboto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
        return cls.session

    @classmethod
    async def send_message(cls, queue_url: str, message: Dict[str, Any]) -> bool:
        """Gửi thông báo đến SQS queue."""
        try:
            session = await cls.get_session()
            async with session.resource('sqs') as sqs_resource:
                queue = await sqs_resource.get_queue_by_url(QueueUrl=queue_url)
                await queue.send_message(MessageBody=json.dumps(message))
                logger.info(f"Đã gửi thông báo đến SQS queue: {queue_url}")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi gửi thông báo đến SQS: {e}")
            return False

    @classmethod
    def close_session(cls):
        """Đóng SQS session."""
        cls.session = None 