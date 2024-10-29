import React, { createContext, useState, useContext, useEffect } from 'react';
import config from './config';

const AuthContext = createContext();

export const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
};

export const deleteCookie = (name) => {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;`;
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState(null);
  const [userId, setUserId] = useState(null)

  useEffect(() => {
    const tokenFromCookie = getCookie('token');
    if (tokenFromCookie) {
      setToken(tokenFromCookie);
    }

    const username = localStorage.getItem('username');
    if (username) {
      setUsername(username);
    }

    const user_id = localStorage.getItem('user_id');
    if (user_id) {
      setUserId(user_id);
    }
  }, []);

  const logout = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
    } catch (e) {
      // ...
    }
    localStorage.removeItem('token');
    localStorage.removeItem("username");
    localStorage.removeItem("user_id");

    deleteCookie('token');
    setUserId(null);
    setUsername(null);
    setToken(null);

    window.location.reload();
  }

  return (
    <AuthContext.Provider value={{ token, username, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
