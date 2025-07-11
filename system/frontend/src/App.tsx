import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import NotificationPermissionPopup from './components/NotificationPermissionPopup';
import DraftReviewPage from './pages/DraftReviewPage';
import Dashboard from './components/Dashboard';
import { DarkModeProvider } from './contexts/DarkModeContext';
import { DraftProvider } from './contexts/DraftContext';

function App() {
  return (
    <DarkModeProvider>
      <DraftProvider>
        <Router>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 flex flex-col">
            <Navigation />
            
            <main className="flex-grow">
              <Routes>
                <Route path="/" element={<DraftReviewPage />} />
                <Route path="/dashboard" element={<Dashboard />} />
              </Routes>
            </main>
            
            <Footer />
            
            <NotificationPermissionPopup />
            
            <ToastContainer 
              position="top-right"
              autoClose={3000}
              hideProgressBar={false}
              newestOnTop={false}
              closeOnClick
              rtl={false}
              pauseOnFocusLoss
              draggable
              pauseOnHover
            />
          </div>
        </Router>
      </DraftProvider>
    </DarkModeProvider>
  );
}

export default App; 