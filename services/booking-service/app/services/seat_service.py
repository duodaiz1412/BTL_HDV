import httpx
import logging
from app.config.settings import SEAT_SERVICE_URL

logger = logging.getLogger("booking-service")

async def update_seat_status(seat_id: str, status: str):
    """Update the status of a seat in the seat service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{SEAT_SERVICE_URL}/seats/{seat_id}/status",
                json={"status": status}
            )
            if response.status_code == 200:
                logger.info(f"Updated seat {seat_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update seat {seat_id}: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error updating seat status: {e}")
        return False

async def update_multiple_seats(seats, status: str):
    """Update the status of multiple seats."""
    results = []
    for seat in seats:
        result = await update_seat_status(seat.seat_id, status)
        results.append(result)
    
    return all(results) 