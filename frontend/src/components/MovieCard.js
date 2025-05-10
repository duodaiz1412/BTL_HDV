import React from 'react';
import { Link } from 'react-router-dom';

const MovieCard = ({ movie }) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <img 
        src={movie.poster_url} 
        alt={movie.title}
        className="w-full h-64 object-cover"
      />
      <div className="p-4">
        <h3 className="text-xl font-semibold mb-2">{movie.title}</h3>
        <p className="text-gray-600 mb-2">{movie.genre}</p>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">{movie.duration} phút</span>
          <span className="text-yellow-500">★ {movie.rating}</span>
        </div>
        <Link 
          to={`/movies/${movie.id}`}
          className="mt-4 block w-full text-center bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
        >
          Xem chi tiết
        </Link>
      </div>
    </div>
  );
};

export default MovieCard; 