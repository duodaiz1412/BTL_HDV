import logging

def setup_logger():
    """
    Thiết lập logging cho API Gateway
    """
    logger = logging.getLogger("api-gateway")
    logger.setLevel(logging.INFO)
    
    # Tạo handler cho console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Định dạng log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Thêm handler vào logger
    logger.addHandler(console_handler)
    
    return logger

# Khởi tạo logger
logger = setup_logger() 