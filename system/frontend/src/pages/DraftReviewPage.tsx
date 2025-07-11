import React from 'react';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { RefreshCw } from 'lucide-react';
import { useDraft } from '../contexts/DraftContext';

const DraftReviewPage: React.FC = () => {
  const {
    isConnected,
    draftQueue,
    currentDraftIndex,
    notificationPermission,
    sendDraftResponse,
    manualReconnect,
    testConnection,
    navigateToDraft,
    requestNotificationPermission
  } = useDraft();

  const currentDraft = draftQueue[currentDraftIndex];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded-full mr-4">
                  <RefreshCw className="h-6 w-6 text-gray-500 dark:text-gray-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                    AI Draft Review
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Review and approve AI-generated email responses.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ConnectionStatus isConnected={isConnected} onReconnect={manualReconnect} />
                
                {/* Notification Status */}
                <div className="flex items-center space-x-2 p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <div className={`w-2 h-2 rounded-full ${
                    notificationPermission === 'granted' ? 'bg-green-500' : 
                    notificationPermission === 'denied' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}></div>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {notificationPermission === 'granted' ? 'Notifications On' : 
                     notificationPermission === 'denied' ? 'Notifications Off' : 'Notifications Pending'}
                  </span>
                  {notificationPermission !== 'granted' && (
                    <button
                      onClick={requestNotificationPermission}
                      className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                    >
                      Enable
                    </button>
                   )}
                 </div>
                 
                 {/* Test Connection Button */}
                 {isConnected && (
                   <button
                     onClick={testConnection}
                     className="px-3 py-2 text-sm font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                   >
                     Test Connection
                   </button>
                 )}
              </div>
            </div>
          </div>

          {draftQueue.length > 0 ? (
            <div className="space-y-6">
              {/* Draft Navigation */}
              {draftQueue.length > 1 && (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Draft {currentDraftIndex + 1} of {draftQueue.length}
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex - 1)}
                          disabled={currentDraftIndex === 0}
                          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                          ← Previous
                        </button>
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex + 1)}
                          disabled={currentDraftIndex === draftQueue.length - 1}
                          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
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
                              : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
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
            <div className="text-center py-20 px-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="bg-gray-100 dark:bg-gray-700 rounded-full p-5 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                <RefreshCw className="h-12 w-12 text-gray-400 dark:text-gray-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
                Waiting for new drafts...
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
                When a new email is processed and requires your review, it will appear here automatically. Ensure your connection is active.
              </p>
              
              {/* Connection Debug Info */}
              <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg text-left max-w-md mx-auto">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Connection Status</h3>
                <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                  <div>WebSocket: <span className={isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>{isConnected ? 'Connected' : 'Disconnected'}</span></div>
                  <div>User ID: <span className="font-mono">default_user</span></div>
                  <div>Notifications: <span className={notificationPermission === 'granted' ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}>{notificationPermission}</span></div>
                  <div>Global Connection: <span className="text-green-600 dark:text-green-400">Active</span></div>
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