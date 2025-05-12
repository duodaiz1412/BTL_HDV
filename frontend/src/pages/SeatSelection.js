import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSeats, bookSeats, createPayment, getMovieById } from '../services/api';

const SeatSelection = () => {
  const { showtimeId } = useParams();
  const navigate = useNavigate();
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [movieInfo, setMovieInfo] = useState(null);
  const [ticketPrice, setTicketPrice] = useState(2000); // Giá mặc định

  // Lấy danh sách ghế và thông tin suất chiếu
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Lấy thông tin ghế
        const seatsResponse = await getSeats(showtimeId);
        setSeats(seatsResponse.data);
        
        // Lấy thông tin suất chiếu (giả sử từ ghế đầu tiên lấy movie_id)
        if (seatsResponse.data.length > 0) {
          const movieId = seatsResponse.data[0].movie_id;
          if (movieId) {
            const movieResponse = await getMovieById(movieId);
            setMovieInfo(movieResponse.data);
          }
        }
        
        console.log('Ghế:', seatsResponse.data);
        setLoading(false);
      } catch (err) {
        console.error('Lỗi khi lấy dữ liệu:', err);
        setError('Không thể tải thông tin');
        setLoading(false);
      }
    };

    fetchData();
  }, [showtimeId]);

  // Xử lý chọn ghế
  const handleSeatClick = (seat) => {
    // Không cho phép chọn ghế đã có trạng thái booked, pending hoặc paid
    if (seat.status === 'booked' || seat.status === 'pending' || seat.status === 'paid') return;

    setSelectedSeats((prev) => {
      if (prev.includes(seat._id)) {
        return prev.filter((s) => s !== seat._id);
      }
      return [...prev, seat._id];
    });
  };

  // Tiến hành đặt vé
  const handleBooking = async () => {
    if (selectedSeats.length === 0) {
      setError('Vui lòng chọn ít nhất một ghế');
      return;
    }

    try {
      // Kiểm tra đăng nhập và lấy customer_id
      const customerId = localStorage.getItem('customer_id');
      if (!customerId) {
        navigate('/login', { state: { returnUrl: `/seats/showtime/${showtimeId}` } });
        return;
      }

      // Lấy movie_id từ localStorage hoặc từ movieInfo
      const savedMovieId = localStorage.getItem('selected_movie_id');
      const movieId = savedMovieId || movieInfo?.id || (seats.length > 0 ? seats[0].movie_id : null);
      
      // Lấy thông tin showtime từ localStorage
      const showtimeValue = localStorage.getItem('selected_showtime');
      
      if (!movieId) {
        setError('Không có thông tin phim');
        return;
      }

      // Tính tổng tiền
      const totalAmount = selectedSeats.length * ticketPrice;

      // Chuẩn bị thông tin ghế với cả seat_id và seat_number
      const formattedSeats = selectedSeats.map(seatId => {
        const seat = seats.find(s => s._id === seatId);
        return {
          seat_id: seatId,
          seat_number: seat ? seat.seat_number : seatId
        };
      });

      // Tạo booking trực tiếp bằng cách sử dụng hàm bookSeats
      try {
        // Sử dụng bookSeats với đầy đủ tham số theo yêu cầu
        const bookingResponse = await bookSeats(
          customerId, 
          movieId, 
          showtimeId,
          showtimeValue, // Thêm thông tin showtime vào booking
          formattedSeats, 
          totalAmount, 
          "pending"
        );
        
        console.log('Booking response:', bookingResponse);
        
        if (!bookingResponse || !bookingResponse.data) {
          setError('Không nhận được phản hồi từ máy chủ khi tạo đơn đặt vé');
          return;
        }

        const bookingId = bookingResponse.data.id || bookingResponse.data._id;
        if (!bookingId) {
          setError('Không tìm thấy ID của đơn đặt vé trong phản hồi');
          return;
        }

        // Chuyển đến trang thanh toán thay vì thanh toán trực tiếp
        navigate(`/payment/${bookingId}`);
      } catch (bookingError) {
        console.error('Lỗi khi tạo booking:', bookingError);
        setError('Không thể tạo đơn đặt vé. Vui lòng thử lại sau.');
        return;
      }
    } catch (err) {
      console.error('Lỗi không xác định khi đặt vé:', err);
      setError('Không thể hoàn tất đặt vé. Vui lòng thử lại sau.');
    }
  };

  // Xử lý khi người dùng quay lại
  const handleGoBack = () => {
    // Xóa showtime_id khỏi localStorage khi quay lại, nhưng giữ lại movie_id
    localStorage.removeItem('selected_showtime_id');
    navigate(-1);
  };

  if (loading) return <div className="text-center p-8">Đang tải...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  // Tạo bố cục ghế trong rạp
  const renderSeatMap = () => {
    // Nhóm ghế theo hàng (A, B, C, ...)
    const seatsByRow = seats.reduce((acc, seat) => {
      const row = seat.seat_number.charAt(0);
      if (!acc[row]) acc[row] = [];
      acc[row].push(seat);
      return acc;
    }, {});

    // Sắp xếp các hàng theo thứ tự
    return Object.keys(seatsByRow).sort().map(row => (
      <div key={row} className="flex mb-2 items-center">
        <div className="w-8 text-center font-bold">{row}</div>
        <div className="flex flex-1 gap-2 justify-center">
          {seatsByRow[row].sort((a, b) => {
            const numA = parseInt(a.seat_number.substring(1));
            const numB = parseInt(b.seat_number.substring(1));
            return numA - numB;
          }).map(seat => {
            // Xác định nếu ghế không khả dụng (đã được đặt hoặc đang chờ thanh toán)
            const isUnavailable = seat.status === 'booked' || seat.status === 'pending' || seat.status === 'paid';
            
            return (
              <button
                key={seat._id}
                onClick={() => handleSeatClick(seat)}
                disabled={isUnavailable}
                className={`
                  w-10 h-10 flex items-center justify-center rounded
                  ${isUnavailable
                    ? seat.status === 'pending' 
                      ? 'bg-yellow-400 cursor-not-allowed' // Ghế đang chờ thanh toán
                      : seat.status === 'paid'
                        ? 'bg-red-500 cursor-not-allowed' // Ghế đã được thanh toán
                        : 'bg-gray-400 cursor-not-allowed' // Ghế đã được đặt
                    : selectedSeats.includes(seat._id)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 hover:bg-gray-300'
                  }
                `}
              >
                {seat.seat_number.substring(1)}
              </button>
            );
          })}
        </div>
      </div>
    ));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6 text-center">Chọn ghế</h1>
      
      {movieInfo && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <h2 className="text-xl font-bold">{movieInfo.title}</h2>
          <p className="text-gray-600 text-sm">{movieInfo.description}</p>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="w-full bg-gray-800 h-2 rounded-lg mb-8"></div>
        <div className="text-center mb-2 text-gray-500">Màn hình</div>
        
        <div className="mt-8">
          {renderSeatMap()}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Thông tin đặt vé</h2>
        
        <div className="mb-4">
          <div className="flex justify-between mb-2">
            <span>Ghế đã chọn:</span>
            <span className="font-medium">
              {selectedSeats.length > 0 
                ? seats
                    .filter(seat => selectedSeats.includes(seat._id))
                    .map(seat => seat.seat_number)
                    .join(', ') 
                : 'Chưa chọn ghế'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Số lượng:</span>
            <span className="font-medium">{selectedSeats.length}</span>
          </div>
          <div className="flex justify-between mt-2">
            <span>Tổng tiền:</span>
            <span className="font-medium text-blue-600">
              {new Intl.NumberFormat('vi-VN', {
                style: 'currency',
                currency: 'VND'
              }).format(selectedSeats.length * ticketPrice)}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2 mt-6">
          <button
            onClick={handleGoBack}
            className="flex-1 py-2 px-4 bg-gray-300 hover:bg-gray-400 rounded"
          >
            Quay lại
          </button>
          <button
            onClick={handleBooking}
            disabled={selectedSeats.length === 0}
            className={`
              flex-1 py-2 px-4 rounded text-white
              ${selectedSeats.length === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600'
              }
            `}
          >
            Tiến hành đặt vé
          </button>
        </div>
      </div>
      
      <div className="mt-6 flex justify-center gap-6">
        <div className="flex items-center">
          <div className="w-6 h-6 bg-gray-200 rounded mr-2"></div>
          <span>Ghế trống</span>
        </div>
        <div className="flex items-center">
          <div className="w-6 h-6 bg-gray-400 rounded mr-2"></div>
          <span>Đã đặt</span>
        </div>
        <div className="flex items-center">
          <div className="w-6 h-6 bg-yellow-400 rounded mr-2"></div>
          <span>Đang chờ thanh toán</span>
        </div>
        <div className="flex items-center">
          <div className="w-6 h-6 bg-red-500 rounded mr-2"></div>
          <span>Đã thanh toán</span>
        </div>
        <div className="flex items-center">
          <div className="w-6 h-6 bg-blue-500 rounded mr-2"></div>
          <span>Đang chọn</span>
        </div>
      </div>
    </div>
  );
};

export default SeatSelection; 