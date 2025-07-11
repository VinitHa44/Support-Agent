import React from 'react';
import { Heart } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 transition-colors duration-200">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col items-center space-y-2">
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <span>Built with</span>
            <Heart className="h-4 w-4 text-red-500 fill-current" />
            <span>by the team</span>
            <span className="font-semibold text-gray-800 dark:text-white">
              Rocket Support Agent
            </span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-500">
            © {currentYear} Rocket Support Agent. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 