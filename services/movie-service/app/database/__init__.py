"""
Database functions cho movie service.
"""
from app.database.mongodb import (
    convert_mongo_id,
    get_movie_by_id,
    create_movie,
    update_movie,
    delete_movie,
    get_all_movies,
    create_showtime,
    get_showtime_by_id,
    get_movie_showtimes,
    update_showtime,
    delete_showtime
) 