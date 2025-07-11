import React, { useState, useEffect } from 'react';
import { Bell, X } from 'lucide-react';

const NotificationPermissionPopup: React.FC = () => {
  const [showPopup, setShowPopup] = useState(false);

  useEffect(() => {
    // Check if user has already seen this popup
    const hasSeenPopup = localStorage.getItem('notificationPopupShown');
    const notificationPermission = Notification.permission;
    
    // Only show if it's the first time and notifications are not already granted
    if (!hasSeenPopup && notificationPermission !== 'granted') {
      setShowPopup(true);
    }
  }, []);

  const handleClose = () => {
    setShowPopup(false);
    localStorage.setItem('notificationPopupShown', 'true');
  };

  if (!showPopup) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 mx-4 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Bell className="h-6 w-6 text-blue-500" />
            <h2 className="text-lg font-semibold text-gray-800 dark:text-white">
              Browser Notifications
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Please enable browser notifications for a seamless experience. You'll receive updates about draft reviews and important notifications.
        </p>
      </div>
    </div>
  );
};

export default NotificationPermissionPopup; 