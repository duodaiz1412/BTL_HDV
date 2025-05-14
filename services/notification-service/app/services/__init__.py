"""
Services cho ứng dụng thông báo.
"""

# Để tránh import circular, đặt các import trong một hàm helper
def get_services():
    from app.services.sqs_service import (
        get_sqs_session,
        receive_sqs_messages,
        delete_sqs_message,
        process_booking_notification,
        process_payment_notification,
        toggle_sqs_processing,
        get_sqs_status,
        ENABLE_SQS_PROCESSING,
        sqs_tasks,
        sqs_session
    )
    
    from app.services.socketio_service import (
        setup_socketio,
        send_notification_to_customer,
        get_active_connections
    )
    
    from app.services.queue_processor import (
        startup,
        shutdown
    )
    
    return {
        'get_sqs_session': get_sqs_session,
        'receive_sqs_messages': receive_sqs_messages,
        'delete_sqs_message': delete_sqs_message,
        'process_booking_notification': process_booking_notification,
        'process_payment_notification': process_payment_notification,
        'toggle_sqs_processing': toggle_sqs_processing,
        'get_sqs_status': get_sqs_status,
        'ENABLE_SQS_PROCESSING': ENABLE_SQS_PROCESSING,
        'sqs_tasks': sqs_tasks,
        'sqs_session': sqs_session,
        'setup_socketio': setup_socketio,
        'send_notification_to_customer': send_notification_to_customer,
        'get_active_connections': get_active_connections,
        'startup': startup,
        'shutdown': shutdown
    }

# Các services được export trực tiếp
from app.services.sqs_service import (
    get_sqs_session,
    receive_sqs_messages,
    delete_sqs_message, 
    toggle_sqs_processing,
    get_sqs_status
)

from app.services.socketio_service import (
    setup_socketio,
    send_notification_to_customer,
    get_active_connections
)

from app.services.queue_processor import (
    startup,
    shutdown
) 