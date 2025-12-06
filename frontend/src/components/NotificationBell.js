import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bell, X } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function NotificationBell({ user }) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  // Fetch unread count
  useEffect(() => {
    if (user) {
      fetchUnreadCount();
      
      // Poll every 30 seconds (not 10 to avoid performance issues)
      const interval = setInterval(fetchUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  // Fetch notifications when dropdown opens
  useEffect(() => {
    if (isOpen && user) {
      fetchNotifications();
    }
  }, [isOpen, user]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/api/notifications/unread-count?user_id=${user.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setUnreadCount(response.data.unread_count || response.data.count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/api/notifications?user_id=${user.id}&limit=50`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      // Show only unread notifications in dropdown (industry standard)
      const unreadNotifications = response.data.filter(n => !n.read);
      setNotifications(unreadNotifications.slice(0, 10)); // Max 10 in dropdown
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.patch(
        `${API}/api/notifications/${notificationId}/read`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update local state
      setNotifications(prev =>
        prev.map(n => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read
    if (!notification.read) {
      markAsRead(notification.id);
    }
    
    // Close dropdown
    setIsOpen(false);
    
    // Navigate
    if (notification.link) {
      navigate(notification.link);
    } else {
      const typeToRoute = {
        'user_registration': '/pending-registrations',
        'user_approved': '/dashboard',
        'project_created': '/projects',
        'drawing_issued': '/projects',
        'drawing_approved': '/projects',
        'drawing_comment': '/projects',
        'contractor_added': '/projects',
        'consultant_added': '/projects',
        'fees_paid_client': '/accounting',
        'fees_received': '/accounting'
      };
      const route = typeToRoute[notification.type] || '/dashboard';
      navigate(route);
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs font-bold rounded-full min-w-[20px] h-5 px-1.5 flex items-center justify-center shadow-lg border-2 border-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Custom Dropdown - NOT using DropdownMenu component */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-slate-200 z-50 max-h-[500px] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50 rounded-t-lg">
            <h3 className="font-semibold text-slate-900">Notifications</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <Bell className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                <p className="text-sm">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {notifications.map((notification) => {
                  const isUnread = !notification.read;
                  return (
                    <div
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification)}
                      className={`p-4 cursor-pointer hover:bg-slate-50 transition-colors ${
                        isUnread ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {isUnread && (
                          <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm text-slate-900 mb-1 ${
                            isUnread ? 'font-bold' : 'font-medium'
                          }`}>
                            {notification.title}
                          </p>
                          <p className={`text-xs mb-2 line-clamp-2 ${
                            isUnread ? 'text-slate-700' : 'text-slate-600'
                          }`}>
                            {notification.message}
                          </p>
                          <p className="text-xs text-slate-400">
                            {formatTimeAgo(notification.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
