import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { DraftData } from '../types/api';
import { Bell, Mail, RefreshCw } from 'lucide-react';

const DraftReviewPage: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [draftQueue, setDraftQueue] = useState<DraftData[]>([]);
  const [currentDraftIndex, setCurrentDraftIndex] = useState(0);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isConnectingRef = useRef(false);
  const userId = 'default_user';

  useEffect(() => {
    connectWebSocket();
    checkNotificationPermission();
    return () => {
      cleanup();
    };
  }, []);

  const cleanup = () => {
    // Clear intervals and timeouts
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Close websocket
    if (wsRef.current) {
      wsRef.current.removeEventListener('open', handleOpen);
      wsRef.current.removeEventListener('message', handleMessage);
      wsRef.current.removeEventListener('close', handleClose);
      wsRef.current.removeEventListener('error', handleError);
      wsRef.current.close();
      wsRef.current = null;
    }
    
    isConnectingRef.current = false;
  };

  const startHeartbeat = () => {
    // Clear any existing heartbeat
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    
    // Send ping every 30 seconds to keep connection alive
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  };

  const stopHeartbeat = () => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  };

  const getReconnectDelay = (attempt: number) => {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
    return Math.min(1000 * Math.pow(2, attempt), 30000);
  };

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
        silent: false
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

  const handleOpen = () => {
    setIsConnected(true);
    console.log('WebSocket connected');
    reconnectAttemptsRef.current = 0; // Reset reconnection attempts
    isConnectingRef.current = false;
    startHeartbeat();
  };

  const handleMessage = (event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      console.error('Raw message:', event.data);
    }
  };

  const handleClose = (event: CloseEvent) => {
    setIsConnected(false);
    isConnectingRef.current = false;
    stopHeartbeat();
    console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
    
    // Only auto-reconnect if it wasn't a manual close (code 1000)
    if (event.code !== 1000) {
      scheduleReconnect();
    }
  };

  const handleError = (error: Event) => {
    console.error('WebSocket error:', error);
    isConnectingRef.current = false;
    stopHeartbeat();
    // Reconnect logic will be triggered by the close event that follows
  };
  
  const connectWebSocket = () => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }
    
    isConnectingRef.current = true;
    
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.hostname + ':8000';
    const wsUrl = `${protocol}//${backendHost}/api/v1/ws/drafts?user_id=${userId}`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.addEventListener('open', handleOpen);
    wsRef.current.addEventListener('message', handleMessage);
    wsRef.current.addEventListener('close', handleClose);
    wsRef.current.addEventListener('error', handleError);
    
    // Set a connection timeout
    const connectionTimeout = setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
        console.log('WebSocket connection attempt timed out.');
        wsRef.current.close(); // This will trigger the handleClose event, which then triggers reconnect
      }
    }, 10000); // 10 second timeout

    wsRef.current.addEventListener('open', () => clearTimeout(connectionTimeout));
  };

  const scheduleReconnect = () => {
    // Don't reconnect if already connecting or max attempts reached
    if (isConnectingRef.current || reconnectAttemptsRef.current >= 10) {
      if (reconnectAttemptsRef.current >= 10) {
        console.log('Max reconnection attempts reached');
        toast.error('Connection failed. Please refresh the page.');
      }
      return;
    }

    const delay = getReconnectDelay(reconnectAttemptsRef.current);
    reconnectAttemptsRef.current++;
    
    console.log(`Scheduling reconnection attempt ${reconnectAttemptsRef.current} in ${delay}ms`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      if (!isConnected && !isConnectingRef.current) {
        connectWebSocket();
      }
    }, delay);
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'draft_review':
        setDraftQueue(prevQueue => [...prevQueue, message.data]);
        
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
      case 'connection_test':
        // Respond to connection test from backend
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'connection_test_response' }));
        }
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
      if (draftQueue.length === 0) {
        toast.warn("No active draft to send a response for.");
        return;
      }
      try {
        wsRef.current.send(JSON.stringify({
          type: 'draft_response',
          data: {
            body: finalDraft
          }
        }));
        // Remove the current draft and reset index if needed
        setDraftQueue(prevQueue => {
          const newQueue = prevQueue.filter((_, index) => index !== currentDraftIndex);
          // Adjust current index if necessary
          if (currentDraftIndex >= newQueue.length && newQueue.length > 0) {
            setCurrentDraftIndex(newQueue.length - 1);
          } else if (newQueue.length === 0) {
            setCurrentDraftIndex(0);
          }
          return newQueue;
        });
        toast.success('Draft response sent successfully!');
      } catch (error) {
        toast.error('Failed to send response. Please check connection.');
        console.error('Send error:', error);
      }
    } else {
      toast.error('WebSocket not connected. Please check your connection.');
    }
  };

  const manualReconnect = () => {
    reconnectAttemptsRef.current = 0;
    cleanup();
    connectWebSocket();
  };

  const navigateToDraft = (index: number) => {
    if (index >= 0 && index < draftQueue.length) {
      setCurrentDraftIndex(index);
    }
  };

  const currentDraft = draftQueue[currentDraftIndex];

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

          {draftQueue.length > 0 ? (
            <div className="space-y-6">
              {/* Draft Navigation */}
              {draftQueue.length > 1 && (
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-semibold text-gray-700">
                        Draft {currentDraftIndex + 1} of {draftQueue.length}
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex - 1)}
                          disabled={currentDraftIndex === 0}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                          ← Previous
                        </button>
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex + 1)}
                          disabled={currentDraftIndex === draftQueue.length - 1}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                          Next →
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {draftQueue.map((_, index) => (
                        <button
                          key={index}
                          onClick={() => navigateToDraft(index)}
                          className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                            index === currentDraftIndex
                              ? 'bg-blue-500'
                              : 'bg-gray-300 hover:bg-gray-400'
                          }`}
                          title={`Go to draft ${index + 1}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              <DraftReviewPanel
                draftData={currentDraft}
                onSend={sendDraftResponse}
                queueCount={draftQueue.length}
              />
            </div>
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
              {!isConnected && (
                <div className="mt-6">
                  <button
                    onClick={manualReconnect}
                    className="flex items-center mx-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200 text-sm font-semibold border border-gray-200"
                  >
                    <RefreshCw size={14} className="mr-2" />
                    Attempt to Reconnect
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPage; 