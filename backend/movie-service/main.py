from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Movie Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.movie_db

# Models
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

class Movie(MovieBase):
    id: str
    created_at: datetime

# Helper functions
def convert_mongo_id(item):
    if item:
        item["id"] = str(item["_id"])
        del item["_id"]
    return item

# Routes
@app.get("/movies")
async def get_movies():
    movies = await db.movies.find().to_list(length=None)
    return [convert_mongo_id(movie) for movie in movies]

@app.get("/movies/{movie_id}")
async def get_movie(movie_id: str):
    try:
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return convert_mongo_id(movie)
    except:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@app.post("/movies", response_model=Movie)
async def create_movie(movie: MovieCreate):
    movie_dict = movie.dict()
    movie_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.movies.insert_one(movie_dict)
    movie_dict["id"] = str(result.inserted_id)
    del movie_dict["_id"]
    
    return movie_dict

@app.put("/movies/{movie_id}")
async def update_movie(movie_id: str, movie: MovieCreate):
    try:
        result = await db.movies.update_one(
            {"_id": ObjectId(movie_id)},
            {"$set": movie.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found")
        return {"message": "Movie updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: str):
    try:
        result = await db.movies.delete_one({"_id": ObjectId(movie_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Movie not found")
        return {"message": "Movie deleted successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

# Showtime routes
@app.post("/showtimes", response_model=Showtime)
async def create_showtime(showtime: ShowtimeCreate):
    # Check if movie exists
    try:
        movie = await db.movies.find_one({"_id": ObjectId(showtime.movie_id)})
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")
    
    showtime_dict = showtime.dict()
    showtime_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.showtimes.insert_one(showtime_dict)
    showtime_dict["id"] = str(result.inserted_id)
    del showtime_dict["_id"]
    
    return showtime_dict

@app.get("/showtimes/{showtime_id}", response_model=Showtime)
async def get_showtime(showtime_id: str):
    try:
        showtime = await db.showtimes.find_one({"_id": ObjectId(showtime_id)})
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return convert_mongo_id(showtime)
    except:
        raise HTTPException(status_code=400, detail="Invalid showtime ID format")

@app.get("/showtimes/movie/{movie_id}")
async def get_movie_showtimes(movie_id: str):
    try:
        showtimes = await db.showtimes.find({"movie_id": movie_id}).to_list(length=None)
        return [convert_mongo_id(showtime) for showtime in showtimes]
    except:
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@app.put("/showtimes/{showtime_id}")
async def update_showtime(showtime_id: str, showtime: ShowtimeCreate):
    try:
        result = await db.showtimes.update_one(
            {"_id": ObjectId(showtime_id)},
            {"$set": showtime.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return {"message": "Showtime updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid showtime ID format")

@app.delete("/showtimes/{showtime_id}")
async def delete_showtime(showtime_id: str):
    try:
        result = await db.showtimes.delete_one({"_id": ObjectId(showtime_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return {"message": "Showtime deleted successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid showtime ID format") 