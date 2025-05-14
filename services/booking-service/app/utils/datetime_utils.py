from datetime import datetime, timedelta

# Múi giờ Hà Nội: UTC+7
HANOI_TIMEZONE_OFFSET = 7

def get_utc_now():
    """Lấy thời gian hiện tại ở múi giờ UTC"""
    return datetime.utcnow()

def get_hanoi_now():
    """Lấy thời gian hiện tại ở múi giờ Hà Nội (UTC+7)"""
    return datetime.utcnow() + timedelta(hours=HANOI_TIMEZONE_OFFSET)

def convert_to_hanoi_timezone(utc_datetime):
    """Chuyển đổi thời gian UTC sang múi giờ Hà Nội (UTC+7)"""
    if isinstance(utc_datetime, datetime):
        return utc_datetime + timedelta(hours=HANOI_TIMEZONE_OFFSET)
    return utc_datetime

def format_datetime(dt, format_str="%d/%m/%Y %H:%M:%S"):
    """Định dạng datetime theo format mong muốn"""
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    return dt

def create_datetime_metadata(dt=None):
    """Tạo metadata về thời gian cho MongoDB"""
    if dt is None:
        dt = get_utc_now()
    
    return {
        "utc": dt,
        "hanoi": convert_to_hanoi_timezone(dt),
        "timezone": "Asia/Ho_Chi_Minh",
        "utc_offset": "+07:00"
    }

def format_mongodb_datetime(mongodb_datetime):
    """Định dạng thời gian từ MongoDB sang chuỗi định dạng Việt Nam"""
    if not isinstance(mongodb_datetime, datetime):
        return mongodb_datetime
    
    # Chuyển sang múi giờ Hà Nội
    hanoi_time = convert_to_hanoi_timezone(mongodb_datetime)
    # Định dạng theo kiểu Việt Nam (ngày/tháng/năm giờ:phút:giây)
    return format_datetime(hanoi_time, "%d/%m/%Y %H:%M:%S") 