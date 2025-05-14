import moment from 'moment';
import 'moment/locale/vi';

/**
 * Cài đặt locale mặc định cho toàn bộ ứng dụng
 */
moment.locale('vi');

/**
 * Định dạng ngày tháng theo kiểu Việt Nam (DD/MM/YYYY)
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Ngày đã định dạng
 */
export const formatDate = (date) => {
  if (!date) return 'Không xác định';
  return moment(date).format('DD/MM/YYYY');
};

/**
 * Định dạng ngày tháng với thời gian theo kiểu Việt Nam
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Ngày và giờ đã định dạng
 */
export const formatDateTime = (date) => {
  if (!date) return 'Không xác định';
  return moment(date).format('DD/MM/YYYY HH:mm');
};

/**
 * Định dạng ngày tháng đầy đủ với tên thứ
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Ngày đã định dạng với tên thứ
 */
export const formatFullDate = (date) => {
  if (!date) return 'Không xác định';
  return moment(date).format('dddd, DD/MM/YYYY');
};

/**
 * Định dạng thời gian (giờ:phút)
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Thời gian đã định dạng
 */
export const formatTime = (date) => {
  if (!date) return 'Không xác định';
  return moment(date).format('HH:mm');
};

/**
 * Trả về thời gian tương đối (ví dụ: 3 giờ trước)
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Thời gian tương đối
 */
export const formatTimeAgo = (date) => {
  if (!date) return 'Không xác định';
  
  // Chuyển đổi sang múi giờ Việt Nam
  const vietnamTime = toVietnamTime(date);
  
  // Nếu thời gian trong tương lai (so với giờ hệ thống), hiển thị thời gian thực tế
  if (vietnamTime.isAfter(moment())) {
    return formatDateTime(date);
  }
  
  return vietnamTime.fromNow();
};

/**
 * Chuyển đổi thời gian từ UTC sang múi giờ Việt Nam
 * @param {string|Date} date - Ngày UTC cần chuyển đổi
 * @returns {moment} Đối tượng moment với múi giờ Việt Nam
 */
export const toVietnamTime = (date) => {
  if (!date) return null;
  
  // Đảm bảo đang làm việc với thời gian UTC
  const utcMoment = moment.utc(date);
  
  // Chuyển đổi sang múi giờ Việt Nam (+7)
  return utcMoment.utcOffset('+07:00');
};

/**
 * Lấy thời gian hiện tại theo múi giờ Việt Nam
 * @returns {moment} Đối tượng moment với thời gian hiện tại ở Việt Nam
 */
export const getNow = () => {
  return moment().utcOffset('+07:00');
};

/**
 * Kiểm tra xem một ngày có phải là ngày trong quá khứ không
 * @param {string|Date} date - Ngày cần kiểm tra
 * @returns {boolean} true nếu là ngày trong quá khứ
 */
export const isPastDate = (date) => {
  if (!date) return false;
  return moment(date).isBefore(moment(), 'day');
};

/**
 * Định dạng thời gian cho API (ISO format)
 * @param {string|Date} date - Ngày cần định dạng
 * @returns {string} Chuỗi thời gian định dạng ISO
 */
export const formatForAPI = (date) => {
  if (!date) return null;
  return moment(date).toISOString();
};

/**
 * Trả về thông tin debug về thời gian
 * @param {string|Date} date - Ngày cần debug
 * @returns {object} Thông tin về thời gian
 */
export const debugTime = (date) => {
  if (!date) return {};
  
  const utcMoment = moment.utc(date);
  const localMoment = moment(date);
  const vietnamMoment = toVietnamTime(date);
  const nowMoment = moment();
  
  return {
    original: date,
    utc: {
      time: utcMoment.format('YYYY-MM-DD HH:mm:ss'),
      iso: utcMoment.toISOString()
    },
    local: {
      time: localMoment.format('YYYY-MM-DD HH:mm:ss'),
      zone: localMoment.format('Z')
    },
    vietnam: {
      time: vietnamMoment.format('YYYY-MM-DD HH:mm:ss'),
      fromNow: vietnamMoment.fromNow()
    },
    now: {
      time: nowMoment.format('YYYY-MM-DD HH:mm:ss'),
      iso: nowMoment.toISOString()
    },
    comparison: {
      isAfter: vietnamMoment.isAfter(nowMoment),
      isBefore: vietnamMoment.isBefore(nowMoment),
      diffMinutes: vietnamMoment.diff(nowMoment, 'minutes'),
      diffHours: vietnamMoment.diff(nowMoment, 'hours')
    }
  };
}; 