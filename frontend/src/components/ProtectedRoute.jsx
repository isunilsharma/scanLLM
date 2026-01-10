import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-12 h-12 border-4 border-gray-300 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // If not authenticated after loading completes, redirect to home
  if (!isAuthenticated) {
    // Check if we just came from OAuth (token in localStorage but not yet validated)
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Give auth context time to validate - show loading
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-primary rounded-full animate-spin"></div>
        </div>
      );
    }
    
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
