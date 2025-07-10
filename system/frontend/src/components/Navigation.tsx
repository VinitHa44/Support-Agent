import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, MessageSquare, Activity, Moon, Sun } from 'lucide-react';
import { useDarkMode } from '../contexts/DarkModeContext';

const Navigation: React.FC = () => {
  const location = useLocation();
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const navigationItems = [
    {
      path: '/',
      name: 'Draft Review',
      icon: MessageSquare,
      description: 'Review and approve email drafts'
    },
    {
      path: '/dashboard',
      name: 'Analytics Dashboard',
      icon: BarChart3,
      description: 'View analytics and statistics'
    }
  ];

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors duration-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg">
              <img 
                src="/agent-logo.svg" 
                alt="Agent Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <h1 className="text-lg font-bold text-gray-800 dark:text-white">
              Support Agent AI
            </h1>
          </div>

          {/* Navigation Links and Dark Mode Toggle */}
          <div className="flex items-center space-x-6">
            <div className="flex space-x-8">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${
                      isActive
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-white'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                    title={item.description}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
            
            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDarkMode ? (
                <Sun className="h-5 w-5 text-yellow-500" />
              ) : (
                <Moon className="h-5 w-5 text-gray-600" />
              )}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 