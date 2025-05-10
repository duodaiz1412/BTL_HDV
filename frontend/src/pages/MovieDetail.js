import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getMovie, getShowtimes, createBooking, createPayment } from '../services/api';
import SeatSelection from '../components/SeatSelection';

const MovieDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [movie, setMovie] = useState(null);
  const [showtimes, setShowtimes] = useState([]);
  const [selectedShowtime, setSelectedShowtime] = useState(null);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [movieRes, showtimesRes] = await Promise.all([
          getMovie(id),
          // getShowtimes(id)
        ]);
        setMovie(movieRes.data);
        // setShowtimes(showtimesRes.data);
      } catch (err) {
        setError('Không thể tải thông tin phim');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleShowtimeSelect = (showtime) => {
    setSelectedShowtime(showtime);
    setSelectedSeats([]);
  };

  const handleSeatsSelected = (seats) => {
    setSelectedSeats(seats);
  };

  const handleBooking = async () => {
    if (!selectedShowtime || selectedSeats.length === 0) {
      setError('Vui lòng chọn suất chiếu và ghế');
      return;
    }

    try {
      // Tạo booking
      const bookingData = {
        movie_id: id,
        showtime_id: selectedShowtime.id,
        seats: selectedSeats,
        total_amount: selectedShowtime.price * selectedSeats.length,
        customer_id: "1" // Tạm thời hardcode customer_id
      };
      const bookingRes = await createBooking(bookingData);

      // Tạo payment
      const paymentData = {
        booking_id: bookingRes.data.id,
        amount: bookingRes.data.total_amount,
        payment_method: "cash"
      };
      await createPayment(paymentData);

      // Chuyển hướng đến trang xác nhận
      navigate(`/bookings/${bookingRes.data.id}`);
    } catch (err) {
      setError('Không thể đặt vé. Vui lòng thử lại sau.');
    }
  };

  if (loading) return <div className="text-center p-8">Đang tải...</div>;
  if (error) return <div className="text-red-500 text-center p-8">{error}</div>;
  if (!movie) return <div className="text-center p-8">Không tìm thấy phim</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <img 
            src={movie.poster_url} 
            alt={movie.title}
            className="w-full rounded-lg shadow-lg"
          />
        </div>
        <div>
          <h1 className="text-3xl font-bold mb-4">{movie.title}</h1>
          <p className="text-gray-600 mb-4">{movie.description}</p>
          <div className="mb-4">
            <p><strong>Thể loại:</strong> {movie.genre || 'Chưa cập nhật'}</p>
            <p><strong>Đạo diễn:</strong> {movie.director || 'Chưa cập nhật'}</p>
            <p><strong>Diễn viên:</strong> {movie.cast ? movie.cast.join(', ') : 'Chưa cập nhật'}</p>
            <p><strong>Thời lượng:</strong> {movie.duration ? `${movie.duration} phút` : 'Chưa cập nhật'}</p>
            <p><strong>Đánh giá:</strong> {movie.rating ? `★ ${movie.rating}` : 'Chưa có đánh giá'}</p>
          </div>

          <div className="mt-8">
            <h2 className="text-xl font-semibold mb-4">Chọn suất chiếu</h2>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {showtimes.map(showtime => (
                <button
                  key={showtime.id}
                  onClick={() => handleShowtimeSelect(showtime)}
                  className={`
                    p-3 rounded text-center
                    ${selectedShowtime?.id === showtime.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 hover:bg-gray-200'
                    }
                  `}
                >
                  {new Date(showtime.time).toLocaleTimeString()}
                </button>
              ))}
            </div>

            {selectedShowtime && (
              <>
                <SeatSelection 
                  showtimeId={selectedShowtime.id}
                  onSeatsSelected={handleSeatsSelected}
                />
                <div className="mt-6">
                  <p className="text-lg mb-2">
                    Tổng tiền: {selectedShowtime.price * selectedSeats.length} VNĐ
                  </p>
                  <button
                    onClick={handleBooking}
                    disabled={selectedSeats.length === 0}
                    className={`
                      w-full py-3 rounded text-white
                      ${selectedSeats.length === 0
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700'
                      }
                    `}
                  >
                    Đặt vé
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetail; 