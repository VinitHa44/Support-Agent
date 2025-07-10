import React from 'react';
import { Wifi, WifiOff } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected }) => {
  return (
    <div className="flex items-center space-x-2 p-2 bg-gray-100 rounded-lg">
      {isConnected ? (
        <>
          <Wifi className="h-5 w-5 text-gray-700" />
          <span className="text-sm font-medium text-gray-800">Connected</span>
        </>
      ) : (
        <>
          <WifiOff className="h-5 w-5 text-gray-500" />
          <span className="text-sm font-medium text-gray-600">Disconnected</span>
        </>
      )}
    </div>
  );
};

export default ConnectionStatus; 