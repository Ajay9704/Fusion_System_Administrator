import { createContext, useContext, useState, useEffect } from 'react';
import { login as loginApi, logout as logoutApi, getCurrentUser } from '../services/authApi';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('accessToken');
      const storedUser = localStorage.getItem('user');

      if (token && storedUser) {
        try {
          // Verify token is still valid by fetching user
          const userData = await getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token invalid, clear storage silently
          localStorage.clear();
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    try {
      const response = await loginApi({ username, password });

      // Save tokens and user data
      localStorage.setItem('accessToken', response.access);
      localStorage.setItem('refreshToken', response.refresh);
      localStorage.setItem('user', JSON.stringify(response.user));

      setUser(response.user);
      return response.user;
    } catch (error) {
      // Enhance error with user-friendly message
      if (error.response?.status === 401) {
        error.userMessage = 'Invalid username or password. Please check your credentials and try again.';
      } else if (error.response?.status === 429) {
        error.userMessage = 'Too many login attempts. Please wait a few minutes before trying again.';
      } else if (error.code === 'ERR_NETWORK') {
        error.userMessage = 'Unable to connect to the server. Please check your internet connection.';
      } else {
        error.userMessage = 'Login failed. Please try again or contact support if the problem persists.';
      }
      throw error;
    }
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch (error) {
      // Silently handle logout errors - we'll clear storage anyway
    } finally {
      // Always clear local storage
      localStorage.clear();
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
