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
          console.log('Initializing auth - validating token...');
          const userData = await getCurrentUser();
          setUser(userData);
          console.log('Auth initialized successfully for:', userData.username);
        } catch (error) {
          console.warn('Token validation failed, clearing storage:', error.message);
          // Token invalid, clear storage
          localStorage.clear();
          setUser(null);
        }
      } else {
        console.log('No existing auth found');
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    try {
      console.log('Attempting login for:', username);
      const response = await loginApi({ username, password });

      console.log('Login successful, user:', response.user.username);
      console.log('Roles:', response.user.roles);
      console.log('Detailed Roles:', response.user.roles_detailed);

      // Enhance user object with role details if available
      const userWithRoleDetails = {
        ...response.user,
        roles_with_details: response.user.roles_detailed || response.user.roles.map(roleName => ({
          name: roleName,
          is_emergency: false,
          role_type: 'permanent'
        }))
      };

      // Save tokens and user data
      localStorage.setItem('accessToken', response.access);
      localStorage.setItem('refreshToken', response.refresh);
      localStorage.setItem('user', JSON.stringify(userWithRoleDetails));

      setUser(userWithRoleDetails);
      return userWithRoleDetails;
    } catch (error) {
      console.error('Login failed:', error.response?.data || error.message);
      throw error;
    }
  };

  const logout = async () => {
    try {
      console.log('Logging out user:', user?.username);
      await logoutApi();
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Always clear local storage
      console.log('Clearing auth data');
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
