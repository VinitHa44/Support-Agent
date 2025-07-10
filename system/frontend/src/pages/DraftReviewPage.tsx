import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { DraftData } from '../types/api';
import { Bell, Mail, Wifi, WifiOff } from 'lucide-react';

const DraftReviewPage: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [draftData, setDraftData] = useState<DraftData | null>(null);
  const [userId, setUserId] = useState('default_user');
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    checkNotificationPermission();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId]);

  const checkNotificationPermission = () => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission !== 'granted') {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
      if (permission === 'granted') {
        toast.success('🔔 Notifications enabled successfully!');
      } else {
        toast.warning('⚠️ Please enable notifications to get draft alerts');
      }
    }
  };

  const sendChromeNotification = (title: string, body: string, icon?: string) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(title, {
        body,
        icon: icon || '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'draft-review',
        requireInteraction: true,
        silent: false,
        vibrate: [200, 100, 200],
        actions: [
          {
            action: 'view',
            title: 'View Draft',
            icon: '/favicon.ico'
          },
          {
            action: 'dismiss',
            title: 'Dismiss',
            icon: '/favicon.ico'
          }
        ]
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      // Auto-close after 10 seconds
      setTimeout(() => {
        notification.close();
      }, 10000);
    }
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use backend port 8000 instead of frontend port 3000
    const backendHost = window.location.hostname + ':8000';
    const wsUrl = `${protocol}//${backendHost}/api/v1/ws/drafts?user_id=${userId}`;
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current?.readyState === WebSocket.CLOSED) {
          connectWebSocket();
        }
      }, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'draft_review':
        setDraftData(message.data);
        
        // Send Chrome notification
        sendChromeNotification(
          '📧 New Draft Ready for Review',
          `Subject: ${message.data.subject}\nFrom: ${message.data.from_email}`,
          '/favicon.ico'
        );
        
        // Show browser notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
          // Additional sound notification (if supported)
          try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmEYEUCJ2O6qe');
            audio.play().catch(() => {
              // Ignore audio errors
            });
          } catch (error) {
            // Ignore audio errors
          }
        }
        break;
      case 'pong':
        console.log('Received pong');
        break;
      case 'error':
        console.error('WebSocket error:', message.data?.message || 'Unknown error');
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendDraftResponse = (finalDraft: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'draft_response',
        data: {
          body: finalDraft
        }
      }));
      
      // Clear draft data after sending
      setDraftData(null);
      toast.success('✅ Draft response sent successfully!');
    } else {
      toast.error('❌ WebSocket not connected. Please check your connection.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100">
      <div className="container mx-auto px-4 py-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-2xl shadow-xl p-6 mb-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-purple-100 p-3 rounded-full mr-4">
                  <Mail className="h-8 w-8 text-purple-600" />
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    🤖 AI Draft Review System
                  </h1>
                  <p className="text-gray-600 text-lg">
                    Review and approve AI-generated email responses
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {/* Connection Status */}
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2">
                    {isConnected ? (
                      <>
                        <div className="bg-green-100 p-2 rounded-full">
                          <Wifi className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-green-600">Connected</span>
                          <div className="h-1 w-16 bg-green-200 rounded-full">
                            <div className="h-1 bg-green-500 rounded-full animate-pulse"></div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="bg-red-100 p-2 rounded-full">
                          <WifiOff className="h-5 w-5 text-red-600" />
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-red-600">Disconnected</span>
                          <div className="h-1 w-16 bg-red-200 rounded-full">
                            <div className="h-1 bg-red-500 rounded-full"></div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Notification Permission */}
                {notificationPermission !== 'granted' && (
                  <button
                    onClick={requestNotificationPermission}
                    className="flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors duration-200 shadow-md"
                  >
                    <Bell className="h-4 w-4 mr-2" />
                    Enable Alerts
                  </button>
                )}
              </div>
            </div>
            
            {/* User ID Input */}
            <div className="mt-6 bg-gray-50 rounded-xl p-4">
              <div className="flex items-center gap-4">
                <label htmlFor="userId" className="text-sm font-semibold text-gray-700 min-w-max">
                  👤 User ID:
                </label>
                <input
                  type="text"
                  id="userId"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm"
                  placeholder="Enter your user ID"
                />
                <div className="flex items-center gap-2">
                  <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Ready' : 'Connecting...'}
                  </span>
                </div>
              </div>
            </div>

            {/* Notification Status */}
            <div className="mt-4 flex items-center justify-between bg-blue-50 rounded-lg p-3">
              <div className="flex items-center">
                <Bell className="h-5 w-5 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-blue-800">
                  Notifications: {notificationPermission === 'granted' ? '✅ Enabled' : '❌ Disabled'}
                </span>
              </div>
              {notificationPermission === 'granted' && (
                <div className="text-xs text-blue-600">
                  You'll receive alerts for new drafts
                </div>
              )}
            </div>
          </div>

          {/* Draft Review Panel */}
          {draftData ? (
            <div className="animate-fadeIn">
              <DraftReviewPanel 
                draftData={draftData} 
                onSendDraft={sendDraftResponse}
              />
            </div>
          ) : (
            <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
              <div className="max-w-md mx-auto">
                <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-full p-6 w-24 h-24 mx-auto mb-6">
                  <svg className="w-12 h-12 text-blue-600 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 7.89a2 2 0 002.83 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  🔍 Waiting for Drafts
                </h3>
                <p className="text-gray-600 mb-6 text-lg">
                  {isConnected 
                    ? '✅ Connected and ready to receive drafts for review' 
                    : '🔄 Connecting to the draft review system...'}
                </p>
                
                {/* Status indicators */}
                <div className="space-y-3">
                  <div className="flex items-center justify-center space-x-2">
                    <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                    <span className="text-sm text-gray-600">
                      {isConnected ? 'WebSocket Connected' : 'Connecting...'}
                    </span>
                  </div>
                  <div className="flex items-center justify-center space-x-2">
                    <div className={`h-3 w-3 rounded-full ${notificationPermission === 'granted' ? 'bg-green-500' : 'bg-orange-500'}`}></div>
                    <span className="text-sm text-gray-600">
                      {notificationPermission === 'granted' ? 'Notifications Ready' : 'Notifications Disabled'}
                    </span>
                  </div>
                </div>

                {/* Tips */}
                <div className="mt-8 bg-blue-50 rounded-xl p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">💡 Tips:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Keep this page open to receive draft notifications</li>
                    <li>• Enable notifications for instant alerts</li>
                    <li>• You'll hear a sound when new drafts arrive</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPage; 