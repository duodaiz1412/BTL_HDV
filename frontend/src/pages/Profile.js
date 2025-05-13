import React, { useState, useEffect } from 'react';
import { getProfile, updateProfile } from '../services/api';
import { toast } from 'react-toastify';
import {
  UserCircleIcon,
  EnvelopeIcon,
  PhoneIcon,
  CalendarIcon,
  PencilSquareIcon,
  KeyIcon,
  FilmIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

const Profile = () => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
  });
  const [stats, setStats] = useState({
    totalBookings: 0,
    totalSpent: 0,
    memberSince: ''
  });

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await getProfile();
        const userData = response.data;
        setProfile(userData);
        setFormData({
          name: userData.name || '',
          email: userData.email || '',
          phone: userData.phone || '',
        });
        
        // Định dạng ngày tạo tài khoản
        const memberSince = userData.created_at 
          ? format(new Date(userData.created_at), 'dd/MM/yyyy', { locale: vi })
          : 'Không xác định';

        setStats(prev => ({
          ...prev,
          memberSince
        }));
        setLoading(false);
      } catch (error) {
        toast.error('Không thể tải thông tin người dùng');
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateProfile(formData);
      setProfile({ ...profile, ...formData });
      setEditing(false);
      toast.success('Cập nhật thông tin thành công');
    } catch (error) {
      toast.error('Không thể cập nhật thông tin');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        {/* Header Section */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-t-2xl p-8 text-white">
          <div className="flex items-center space-x-6">
            <div className="relative">
              <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center">
                <UserCircleIcon className="w-20 h-20 text-blue-500" />
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-bold">{profile.name}</h1>
              <p className="text-blue-100 mt-1">Thành viên từ {stats.memberSince}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-b-2xl shadow-lg p-6">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Thông tin cá nhân */}
            <div className="md:col-span-2 space-y-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Thông tin cá nhân</h2>
                <button
                  onClick={() => setEditing(!editing)}
                  className="flex items-center text-blue-600 hover:text-blue-700"
                >
                  <PencilSquareIcon className="w-5 h-5 mr-1" />
                  {editing ? 'Hủy' : 'Chỉnh sửa'}
                </button>
              </div>

              {editing ? (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Họ và tên
                      </label>
                      <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                        disabled
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Số điện thoại
                      </label>
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setEditing(false)}
                      className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Lưu thay đổi
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="flex items-center space-x-3">
                      <EnvelopeIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Email</p>
                        <p className="font-medium">{profile.email}</p>
                      </div>

                    </div>
                    <div className="flex items-center space-x-3">
                      <PhoneIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Số điện thoại</p>
                        <p className="font-medium">{profile.phone || 'Chưa cập nhật'}</p>
                      </div>

                    </div>
                    <div className="flex items-center space-x-3">
                      <CalendarIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Ngày tham gia</p>
                        <p className="font-medium">{stats.memberSince}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Thống kê hoạt động */}
              <div className="mt-8">
                <h2 className="text-xl font-semibold mb-4">Thống kê hoạt động</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <FilmIcon className="w-8 h-8 text-blue-500 mb-2" />
                    <p className="text-sm text-gray-600">Tổng số vé đã đặt</p>
                    <p className="text-2xl font-bold text-blue-600">{stats.totalBookings}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <CurrencyDollarIcon className="w-8 h-8 text-green-500 mb-2" />
                    <p className="text-sm text-gray-600">Tổng chi tiêu</p>
                    <p className="text-2xl font-bold text-green-600">
                      {stats.totalSpent.toLocaleString()} VND
                    </p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <UserCircleIcon className="w-8 h-8 text-purple-500 mb-2" />
                    <p className="text-sm text-gray-600">ID Thành viên</p>
                    <p className="text-sm font-medium text-purple-600 break-all">{profile.id}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Đổi mật khẩu */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Bảo mật</h2>
              <div className="mt-8">
                <button
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  <KeyIcon className="w-5 h-5 text-gray-500" />
                  <span>Đổi mật khẩu</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile; 