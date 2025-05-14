"""
Định nghĩa các model cho movie service.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ShowtimeBase(BaseModel):
    movie_id: str
    time: datetime
    theater: str
    price: float

class ShowtimeCreate(ShowtimeBase):
    pass

class Showtime(ShowtimeBase):
    id: str
    created_at: datetime

class MovieBase(BaseModel):
    title: str
    description: str
    duration: int
    genre: str
    director: str
    cast: List[str]
    release_date: datetime
    poster_url: str
    trailer_url: str
    rating: float

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    genre: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[List[str]] = None
    release_date: Optional[datetime] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    rating: Optional[float] = None

class Movie(MovieBase):
    id: str
    created_at: datetime 