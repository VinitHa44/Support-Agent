import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { DraftData } from '../types/api';

const DraftReviewPage: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [draftData, setDraftData] = useState<DraftData | null>(null);
  const [userId, setUserId] = useState('default_user');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId]);

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use backend port 8000 instead of frontend port 3000
    const backendHost = window.location.hostname + ':8000';
    const wsUrl = `${protocol}//${backendHost}/api/v1/ws/drafts?user_id=${userId}`;
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      toast.success('Connected to draft review system');
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      toast.warning('Disconnected from draft review system');
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
      toast.error('WebSocket connection error');
    };
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'draft_review':
        setDraftData(message.data);
        toast.info('New drafts received for review');
        // Show browser notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('New drafts for review', {
            body: `Subject: ${message.data.subject}`,
            icon: '/favicon.ico'
          });
        }
        break;
      case 'pong':
        console.log('Received pong');
        break;
      case 'error':
        toast.error(`Error: ${message.data.message}`);
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
      toast.success('Draft response sent successfully');
    } else {
      toast.error('WebSocket not connected');
    }
  };

  const requestNotificationPermission = () => {
    if ('Notification' in window && Notification.permission !== 'granted') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          toast.success('Notifications enabled');
        }
      });
    }
  };

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-white shadow-sm rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Draft Review System
                </h1>
                <p className="text-gray-600">
                  Review and approve email drafts for customer support
                </p>
              </div>
              <ConnectionStatus isConnected={isConnected} />
            </div>
            
            {/* User ID Input */}
            <div className="mt-4 flex items-center gap-4">
              <label htmlFor="userId" className="text-sm font-medium text-gray-700">
                User ID:
              </label>
              <input
                type="text"
                id="userId"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter user ID"
              />
            </div>
          </div>

          {/* Draft Review Panel */}
          {draftData ? (
            <DraftReviewPanel 
              draftData={draftData} 
              onSendDraft={sendDraftResponse}
            />
          ) : (
            <div className="bg-white shadow-sm rounded-lg p-12 text-center">
              <div className="text-gray-500">
                <svg className="mx-auto h-12 w-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 7.89a2 2 0 002.83 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Waiting for drafts
                </h3>
                <p className="text-gray-600 mb-4">
                  {isConnected 
                    ? 'Connected and ready to receive drafts for review' 
                    : 'Connecting to draft review system...'}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPage; 