import logging

def setup_logger():
    """
    Cấu hình và trả về logger cho ứng dụng
    """
    logger = logging.getLogger("seat-service")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger 