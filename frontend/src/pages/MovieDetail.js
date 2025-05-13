import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getMovieById, getShowtimes } from '../services/api';
import {
  ClockIcon,
  FilmIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  TicketIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

const MovieDetail = () => {
  const { movieId } = useParams();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [showtimes, setShowtimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);

  useEffect(() => {
    const fetchMovieDetails = async () => {
      try {
        const [movieResponse, showtimesResponse] = await Promise.all([
          getMovieById(movieId),
          getShowtimes(movieId)
        ]);
        setMovie(movieResponse.data);
        
        // Nhóm suất chiếu theo ngày
        const groupedShowtimes = showtimesResponse.data.reduce((acc, showtime) => {
          const date = new Date(showtime.time).toLocaleDateString();
          if (!acc[date]) {
            acc[date] = [];
          }
          acc[date].push(showtime);
          return acc;
        }, {});
        
        setShowtimes(groupedShowtimes);
        setSelectedDate(Object.keys(groupedShowtimes)[0]); // Chọn ngày đầu tiên
        setLoading(false);
      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError('Không thể tải thông tin phim');
        setLoading(false);
      }
    };

    fetchMovieDetails();
  }, [movieId]);

  const handleBookSeats = (showtimeId, showtimeTime) => {
    localStorage.setItem('selected_movie_id', movieId);
    localStorage.setItem('selected_showtime_id', showtimeId);
    localStorage.setItem('selected_showtime', showtimeTime);
    navigate(`/seats/showtime/${showtimeId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-red-500">
          <InformationCircleIcon className="w-12 h-12 mx-auto mb-2" />
          <p className="text-xl font-semibold">{error}</p>
        </div>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-gray-500">
          <FilmIcon className="w-12 h-12 mx-auto mb-2" />
          <p className="text-xl font-semibold">Không tìm thấy phim</p>
        </div>
      </div>
    );
  }

  const formatShowtime = (time) => {
    try {
      return format(new Date(time), 'HH:mm', { locale: vi });
    } catch (error) {
      return 'Thời gian không hợp lệ';
    }
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return format(date, 'EEEE, dd/MM/yyyy', { locale: vi });
    } catch (error) {
      return dateStr;
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div 
        className="relative h-96 bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url(${movie.poster_url})`
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 to-transparent"></div>
        <div className="container mx-auto px-4 h-full flex items-end pb-8">
          <div className="flex flex-col md:flex-row items-end gap-8 text-white relative z-10">
            <img
              src={movie.poster_url}
              alt={movie.title}
              className="w-64 rounded-lg shadow-2xl hidden md:block"
            />
            <div className="flex-1">
              <h1 className="text-4xl font-bold mb-4">{movie.title}</h1>
              <div className="flex flex-wrap gap-4 text-sm mb-4">
                <span className="flex items-center">
                  <ClockIcon className="w-5 h-5 mr-1" />
                  120 phút
                </span>
                <span className="flex items-center">
                  <FilmIcon className="w-5 h-5 mr-1" />
                  {movie.genre || 'Phim mới'}
                </span>
              </div>
              <p className="text-gray-300 text-lg leading-relaxed">
                {movie.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Showtimes Section */}
      <div className="container mx-auto px-4 py-12">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <CalendarIcon className="w-6 h-6 mr-2 text-blue-500" />
            Lịch chiếu phim
          </h2>

          {/* Date Selection */}
          <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
            {Object.keys(showtimes).map((date) => (
              <button
                key={date}
                onClick={() => setSelectedDate(date)}
                className={`px-4 py-2 rounded-lg flex-shrink-0 transition-colors duration-200 ${
                  selectedDate === date
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                {formatDate(date)}
              </button>
            ))}
          </div>

          {/* Showtimes Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {selectedDate && showtimes[selectedDate]?.map((showtime) => (
              <div
                key={showtime.id}
                className="bg-gray-50 rounded-lg p-6 hover:shadow-lg transition-shadow duration-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <p className="text-xl font-semibold text-blue-600">
                      {formatShowtime(showtime.time)}
                    </p>
                    <p className="text-gray-600 flex items-center mt-1">
                      <FilmIcon className="w-4 h-4 mr-1" />
                      {showtime.theater}
                    </p>
                  </div>
                  <span className="flex items-center text-green-600 font-semibold">
                    <CurrencyDollarIcon className="w-5 h-5 mr-1" />
                    {formatCurrency(showtime.price)}
                  </span>
                </div>

                <button
                  onClick={() => handleBookSeats(showtime.id, showtime.time)}
                  className="w-full flex items-center justify-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200"
                >
                  <TicketIcon className="w-5 h-5 mr-2" />
                  Đặt vé ngay
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetail;