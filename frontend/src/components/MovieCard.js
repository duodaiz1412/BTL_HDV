import React from 'react';
import { Link } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  // Hàm để lưu movie_id vào localStorage
  const handleMovieClick = () => {
    localStorage.setItem('selected_movie_id', movie.id);
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <img
        src={movie.poster_url}
        alt={movie.title}
        className="w-full h-64 object-cover"
      />
      <div className="p-4">
        <h3 className="text-xl font-semibold mb-2">{movie.title}</h3>
        <p className="text-gray-600 mb-4">{movie.description}</p>
        <div className="flex justify-between items-center">
          <span className="text-gray-500">{movie.duration} minutes</span>
          <Link
            to={`/movies/${movie.id}`}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={handleMovieClick}
          >
            Book Now
          </Link>
        </div>
      </div>
    </div>
  );
};

export default MovieCard; 