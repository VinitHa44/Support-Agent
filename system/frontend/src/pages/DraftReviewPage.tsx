import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { DraftData } from '../types/api';
import { Bell, Mail, Wifi, WifiOff } from 'lucide-react';

const DraftReviewPage: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [draftData, setDraftData] = useState<DraftData | null>(null);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  const wsRef = useRef<WebSocket | null>(null);
  const userId = 'default_user';

  useEffect(() => {
    connectWebSocket();
    checkNotificationPermission();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

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
        toast.success('Notifications enabled successfully!');
      } else {
        toast.warning('Please enable notifications to get draft alerts');
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
          'New Draft Ready for Review',
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
      toast.success('Draft response sent successfully!');
    } else {
      toast.error('WebSocket not connected. Please check your connection.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-white border border-gray-200 p-2 rounded-full mr-4">
                  <Mail className="h-6 w-6 text-gray-500" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800">
                    AI Draft Review
                  </h1>
                  <p className="text-sm text-gray-500">
                    Review and approve AI-generated email responses.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {notificationPermission !== 'granted' && (
                  <button
                    onClick={requestNotificationPermission}
                    className="flex items-center px-3 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-xs font-semibold"
                  >
                    <Bell size={14} className="mr-2" />
                    Enable Alerts
                  </button>
                )}
                <ConnectionStatus isConnected={isConnected} />
              </div>
            </div>
          </div>

          {draftData ? (
            <DraftReviewPanel 
              draftData={draftData} 
              onSend={sendDraftResponse} 
            />
          ) : (
            <div className="text-center py-20 px-6 bg-white rounded-lg border border-gray-200">
              <div className="bg-gray-100 rounded-full p-5 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                <Mail className="h-12 w-12 text-gray-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                Waiting for new drafts...
              </h2>
              <p className="text-sm text-gray-500 max-w-sm mx-auto">
                When a new email is processed and requires your review, it will appear here automatically. Ensure your connection is active.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPage; 