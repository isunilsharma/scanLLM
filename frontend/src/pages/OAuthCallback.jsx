import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (!code || !state) {
      navigate('/?error=oauth_failed');
      return;
    }

    // Call backend callback to exchange code for token
    axios.get(`${BACKEND_URL}/api/auth/github/callback`, {
      params: { code, state }
    })
    .then(response => {
      const { token, user, redirect_to } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect to app
      window.location.href = redirect_to || '/app/repos';
    })
    .catch(error => {
      console.error('OAuth callback failed:', error);
      navigate('/?error=oauth_failed');
    });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-gray-300 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Completing sign-in...</h2>
        <p className="text-gray-600">Please wait</p>
      </div>
    </div>
  );
};

export default OAuthCallback;
