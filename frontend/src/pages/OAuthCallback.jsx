import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState(null);

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (!code || !state) {
      navigate('/?error=oauth_failed');
      return;
    }

    // Call backend callback to exchange code for token
    handleOAuthCallback(code, state);
  }, []);

  const handleOAuthCallback = async (code, state) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/github/callback`, {
        params: { code, state }
      });
      
      const { token, user, redirect_to } = response.data;
      
      // Store token and user in localStorage
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Small delay to ensure localStorage is written
      setTimeout(() => {
        window.location.href = redirect_to || '/app/repos';
      }, 100);
      
    } catch (err) {
      console.error('OAuth callback failed:', err);
      setError(err.response?.data?.detail || 'Authentication failed');
      
      setTimeout(() => {
        navigate('/?error=oauth_failed');
      }, 3000);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Failed</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">Redirecting to homepage...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-gray-300 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Completing sign-in...</h2>
        <p className="text-gray-600">Storing your session securely</p>
      </div>
    </div>
  );
};

export default OAuthCallback;
