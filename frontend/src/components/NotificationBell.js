import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell } from 'lucide-react';
import { toast } from 'sonner';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function NotificationBell({ user }) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (user) {
      // Fetch initial count
      fetchUnreadCount();
      
      // Poll for new notifications every 10 seconds
      const interval = setInterval(() => {
        fetchUnreadCount();
        checkForNewNotifications();
      }, 10000);
      
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/notifications/unread-count?user_id=${user.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.unread_count || response.data.count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  const checkForNewNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/notifications?user_id=${user.id}&unread_only=true`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const newNotifications = response.data;
      
      // Show toast for new notifications (only if different from current)
      if (newNotifications.length > 0 && notifications.length > 0) {
        const latestNotification = newNotifications[0];
        const isNew = !notifications.some(n => n.id === latestNotification.id);
        
        if (isNew) {
          toast.info(latestNotification.title, {
            description: latestNotification.message,
            duration: 5000,
          });
        }
      }
      
      setNotifications(newNotifications);
    } catch (error) {
      console.error('Error checking notifications:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/notifications?user_id=${user.id}&limit=20`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/api/notifications/${notificationId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local state
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/api/notifications/mark-all-read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      console.error('Error marking all as read:', error);
      toast.error('Failed to mark notifications as read');
    }
  };

  const handleNotificationClick = (notification) => {
    // Mark as read
    markAsRead(notification.id);
    
    // Close dropdown
    setOpen(false);
    
    // Navigate based on notification link or type
    if (notification.link) {
      window.location.href = notification.link;
    } else {
      // Fallback navigation based on notification type
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
      window.location.href = route;
    }
  };

  const handleOpenChange = (isOpen) => {
    setOpen(isOpen);
    if (isOpen) {
      fetchNotifications();
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <DropdownMenu open={open} onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger asChild>
        <button className="relative p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-slate-600" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs font-bold rounded-full min-w-[20px] h-5 px-1 flex items-center justify-center shadow-lg border-2 border-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        className="w-96 max-h-[500px] overflow-y-auto p-0" 
        align="end"
        onInteractOutside={(e) => {
          // Prevent closing when clicking inside
          e.preventDefault();
        }}
      >
        <div className="p-3 border-b border-slate-200 flex items-center justify-between sticky top-0 bg-white z-10">
          <h3 className="font-semibold text-slate-900">Notifications</h3>
          {unreadCount > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                markAllAsRead();
              }}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              Mark all as read
            </button>
          )}
        </div>
        
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <Bell className="w-12 h-12 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">No notifications</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => {
              const isUnread = !notification.read && !notification.is_read;
              return (
                <div
                  key={notification.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleNotificationClick(notification);
                  }}
                  className={`p-3 cursor-pointer hover:bg-slate-50 transition-colors ${
                    isUnread ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {isUnread && (
                      <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm text-slate-900 ${isUnread ? 'font-bold' : 'font-medium'}`}>
                        {notification.title}
                      </p>
                      <p className={`text-xs mt-1 line-clamp-2 ${isUnread ? 'text-slate-700' : 'text-slate-600'}`}>
                        {notification.message}
                      </p>
                      {notification.project_name && (
                        <p className="text-xs text-slate-500 mt-1">
                          📁 {notification.project_name}
                        </p>
                      )}
                      <p className="text-xs text-slate-400 mt-1">
                        {formatTimeAgo(notification.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
