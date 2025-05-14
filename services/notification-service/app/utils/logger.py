"""
Logger configuration
"""
import logging

def setup_logger():
    """
    Cài đặt và cấu hình logger cho ứng dụng.
    """
    logger = logging.getLogger("notification-service")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger 