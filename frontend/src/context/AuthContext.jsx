import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios to always include Authorization header if token exists
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token && config.url?.includes(BACKEND_URL)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user');
    
    if (!token) {
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      return;
    }

    try {
      // Verify token is still valid
      const response = await axios.get(`${API}/github/user`);
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      // Token invalid or expired
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    // OAuth endpoint is at /api/auth/github/login (routed to backend)
    window.location.href = `${BACKEND_URL}/api/auth/github/login`;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/github/revoke`);
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Always clear local storage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setUser(null);
      setIsAuthenticated(false);
      window.location.href = '/';
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
