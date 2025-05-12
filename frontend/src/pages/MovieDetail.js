import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getMovieById, getShowtimes } from '../services/api';

const MovieDetail = () => {
  const { movieId } = useParams();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [showtimes, setShowtimes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMovieDetails = async () => {
      try {
        const [movieResponse, showtimesResponse] = await Promise.all([
          getMovieById(movieId),
          getShowtimes(movieId)
        ]);
        setMovie(movieResponse.data);
        setShowtimes(showtimesResponse.data);
        console.log('Showtimes data:', showtimesResponse.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError('Failed to fetch movie details');
        setLoading(false);
      }
    };

    fetchMovieDetails();
  }, [movieId]);

  // Điều hướng đến trang chọn ghế
  const handleBookSeats = (showtimeId, showtimeTime) => {
    // Cập nhật movie_id vào localStorage khi người dùng chọn showtime
    // Không cần xóa movie_id tại đây, vì chúng ta vẫn cần nó cho đến khi đặt vé xong
    localStorage.setItem('selected_movie_id', movieId);
    localStorage.setItem('selected_showtime_id', showtimeId);
    localStorage.setItem('selected_showtime', showtimeTime); // Lưu thời gian chiếu vào localStorage
    navigate(`/seats/showtime/${showtimeId}`);
  };

  // Không xóa movie_id khi unmount component này nữa
  // movie_id sẽ được xóa sau khi hoàn tất đặt vé hoặc hủy đặt vé

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;
  if (!movie) return <div className="text-center p-8">Movie not found</div>;

  // Hàm định dạng thời gian hợp lệ
  const formatDateTime = (dateTimeStr) => {
    try {
      const date = new Date(dateTimeStr);
      if (isNaN(date.getTime())) {
        return {
          date: 'Thời gian không hợp lệ',
          time: ''
        };
      }
      return {
        date: date.toLocaleDateString(),
        time: date.toLocaleTimeString()
      };
    } catch (error) {
      return {
        date: 'Thời gian không hợp lệ',
        time: ''
      };
    }
  };

  // Hàm định dạng tiền tệ
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(amount);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row gap-8">
        <div className="md:w-1/3">
          <img
            src={movie.poster_url}
            alt={movie.title}
            className="w-full rounded-lg shadow-lg"
          />
        </div>
        <div className="md:w-2/3">
          <h1 className="text-3xl font-bold mb-4">{movie.title}</h1>
          <p className="text-gray-600 mb-4">{movie.description}</p>
          <div className="mb-4">
            <h2 className="text-xl font-semibold mb-2">Lịch chiếu phim</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {showtimes.map((showtime) => {
                const formattedTime = formatDateTime(showtime.time);
                return (
                  <div
                    key={showtime.id}
                    className="border rounded p-4 hover:bg-gray-50"
                  >
                    <p className="font-semibold">{formattedTime.date}</p>
                    <p className="text-gray-600 mb-2">{formattedTime.time}</p>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-700">
                        <i className="fas fa-film mr-1"></i> {showtime.theater}
                      </span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(showtime.price)}
                      </span>
                    </div>
                    <button
                      onClick={() => handleBookSeats(showtime.id, showtime.time)}
                      className="mt-2 w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
                    >
                      Đặt vé
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetail; 