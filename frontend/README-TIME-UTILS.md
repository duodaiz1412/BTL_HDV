# Tiện ích xử lý thời gian trong ứng dụng

Đây là hướng dẫn về cách xử lý thời gian trong dự án frontend.

## Tổng quan

Dự án sử dụng thư viện [moment.js](https://momentjs.com/) để định dạng thời gian. Tất cả các hàm xử lý thời gian được tập trung trong module `src/utils/dateUtils.js` để đảm bảo tính nhất quán.

## Cài đặt

Moment.js đã được cài đặt qua yarn:

```bash
yarn add moment
```

Tiếng Việt đã được cài đặt (locale):

```javascript
import 'moment/locale/vi';
moment.locale('vi');
```

## Các hàm xử lý thời gian

| Hàm | Mô tả | Sử dụng |
|-----|-------|---------|
| `formatDate` | Định dạng ngày (DD/MM/YYYY) | `formatDate(date)` |
| `formatDateTime` | Định dạng ngày và giờ (DD/MM/YYYY HH:mm) | `formatDateTime(date)` |
| `formatFullDate` | Định dạng đầy đủ có tên thứ (thứ Hai, 01/01/2023) | `formatFullDate(date)` |
| `formatTime` | Định dạng giờ (HH:mm) | `formatTime(date)` |
| `formatTimeAgo` | Hiển thị thời gian tương đối (3 giờ trước) | `formatTimeAgo(date)` |
| `toVietnamTime` | Chuyển đổi sang múi giờ Việt Nam (+7) | `toVietnamTime(date)` |
| `getNow` | Lấy thời gian hiện tại theo múi giờ Việt Nam | `getNow()` |
| `isPastDate` | Kiểm tra xem ngày có phải trong quá khứ | `isPastDate(date)` |
| `formatForAPI` | Định dạng thời gian cho API (ISO) | `formatForAPI(date)` |

## Ví dụ sử dụng

```javascript
import { formatDateTime, formatTimeAgo } from '../utils/dateUtils';

// Trong component
return (
  <div>
    <p>Ngày đặt vé: {formatDateTime(booking.created_at)}</p>
    <p>Thời gian thanh toán: {formatTimeAgo(booking.paid_at)}</p>
  </div>
);
```

## Chuyển đổi UTC sang múi giờ Việt Nam

Dữ liệu thời gian từ backend thường được lưu dưới dạng UTC. Để hiển thị theo múi giờ Việt Nam, sử dụng:

```javascript
import { toVietnamTime, formatDateTime } from '../utils/dateUtils';

// Chuyển đổi thời gian từ UTC sang múi giờ Việt Nam
const localTime = toVietnamTime(utcTimeFromBackend);

// Định dạng và hiển thị
const formattedTime = formatDateTime(localTime);
```

## Xử lý múi giờ trong form

Khi gửi dữ liệu thời gian lên API, nên chuyển về dạng ISO:

```javascript
import { formatForAPI } from '../utils/dateUtils';

const handleSubmit = () => {
  const data = {
    // ... other fields
    scheduled_time: formatForAPI(selectedDate)
  };
  
  // Send to API
  api.post('/endpoint', data);
};
```

## Tổng kết

- Luôn sử dụng các hàm từ `dateUtils.js` thay vì xử lý trực tiếp.
- Nếu cần thêm các định dạng mới, hãy bổ sung vào `dateUtils.js`.
- Lưu ý sự khác biệt giữa múi giờ UTC (backend) và múi giờ Việt Nam (frontend). 