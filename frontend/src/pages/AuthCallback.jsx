import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    console.log('AuthCallback: Received code and state from GitHub');

    if (!code || !state) {
      console.error('AuthCallback: Missing code or state parameter');
      setStatus('error');
      setTimeout(() => navigate('/?error=oauth_failed'), 2000);
      return;
    }

    try {
      console.log('AuthCallback: Calling backend to exchange code for token...');
      
      // Call backend to exchange code for token
      const response = await axios.post(
        `${BACKEND_URL}/api/auth/github/exchange`,
        { code, state }
      );

      const { token, user } = response.data;
      
      console.log('AuthCallback: Token received from backend');
      console.log('AuthCallback: User:', user.login);

      // Store in localStorage (on scanllm.ai domain!)
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      console.log('AuthCallback: Token and user stored in localStorage');
      console.log('AuthCallback: Redirecting to /app/repos');

      // Small delay then redirect
      setTimeout(() => {
        navigate('/app/repos');
      }, 200);
      
    } catch (error) {
      console.error('AuthCallback: Exchange failed', error);
      setStatus('error');
      setTimeout(() => navigate('/?error=oauth_failed'), 3000);
    }
  };

  if (status === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Failed</h2>
          <p className="text-gray-600">Redirecting to homepage...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-gray-300 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Completing sign-in...</h2>
        <p className="text-gray-600">Storing your session on scanllm.ai...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
