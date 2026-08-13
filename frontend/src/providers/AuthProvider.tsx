import React, { useEffect } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { authService } from '../services/auth.service';
import { useAuthStore } from '../stores/AuthStore';
import { LoginFormData, RegisterFormData } from '../utils/validationHelpers';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, tokens, isAuthenticated, isLoading, error, setAuth, setUser, logout, setLoading, setError } =
    useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      if (tokens?.access_token && !user) {
        setLoading(true);
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch {
          logout();
        } finally {
          setLoading(false);
        }
      }
    };
    initAuth();
  }, []);

  const handleLogin = async (credentials: LoginFormData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await authService.login(credentials);
      setAuth(res.user, { access_token: res.access_token, token_type: res.token_type });
      return res;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Login failed. Please verify credentials.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (data: RegisterFormData) => {
    setLoading(true);
    setError(null);
    try {
      const res = await authService.register(data);
      if (res.access_token && res.user) {
        setAuth(res.user, { access_token: res.access_token, token_type: res.token_type });
      }
      return res;
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      console.warn('Failed to refresh user profile', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tokens,
        isAuthenticated,
        isLoading,
        error,
        login: handleLogin,
        register: handleRegister,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
