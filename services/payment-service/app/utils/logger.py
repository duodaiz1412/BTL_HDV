import logging

def setup_logger():
    """Cấu hình và trả về logger."""
    logger = logging.getLogger("payment-service")
    
    # Cấu hình log level
    logger.setLevel(logging.INFO)
    
    # Tạo handler và formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Thêm handler vào logger
    logger.addHandler(handler)
    
    return logger 