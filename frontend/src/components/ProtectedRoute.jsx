import React, { useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, checkAuth } = useAuth();
  const hasTriggeredRecheck = useRef(false);

  // If token exists in localStorage but auth state says not authenticated,
  // trigger a re-check once (fixes race condition on first load)
  useEffect(() => {
    if (!loading && !isAuthenticated && !hasTriggeredRecheck.current) {
      const token = localStorage.getItem('auth_token');
      if (token) {
        console.log('ProtectedRoute: Token exists but not authenticated, re-checking...');
        hasTriggeredRecheck.current = true;
        checkAuth();
      }
    }
  }, [loading, isAuthenticated, checkAuth]);

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-12 h-12 border-4 border-gray-300 border-t-primary rounded-full animate-spin"></div>
      </div>
    );
  }

  // If not authenticated after loading completes, check for token
  if (!isAuthenticated) {
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Token exists - show loading while checkAuth re-validates
      // (the useEffect above will trigger re-check)
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
