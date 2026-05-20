import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUserLoggedIn = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await api.get('/user/profile');
          setUser(res.data.data);
        } catch (error) {
          console.error('Error fetching profile', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    checkUserLoggedIn();
  }, []);

  const login = async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    const payload = res.data.data;
    localStorage.setItem('token', payload.token);
    setUser(payload.user);
    return payload;
  };

  const register = async (username, email, password) => {
    const res = await api.post('/auth/register', { username, email, password });
    return res.data;
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
