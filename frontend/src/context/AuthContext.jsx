import { createContext, useState, useContext, useEffect } from 'react';
import { login as loginApi, register as registerApi, getCurrentUser } from '../services/api';

const AuthContext = createContext({
  user: null,
  login: () => {},
  register: () => {},
  logout: () => {},
  loading: true
});

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

  useEffect(() => {
    checkAuth();
    // Listen for global auth-logout (e.g., 401 from axios interceptor)
    const onLogout = () => {
      setUser(null);
    };
    window.addEventListener('auth-logout', onLogout);
    return () => window.removeEventListener('auth-logout', onLogout);
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await getCurrentUser();
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('token');
      }
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await loginApi(formData);
    localStorage.setItem('token', response.data.access_token);
    
    const userResponse = await getCurrentUser();
    setUser(userResponse.data);
    return userResponse.data;
  };

  const register = async (userData) => {
    const response = await registerApi(userData);
    // Auto login after registration
    await login(userData.username, userData.password);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};