import { create } from 'zustand';
import { ENV } from '../config/env.config';
import { AuthState, AuthTokens, UserProfile } from '../types/auth.types';

interface AuthStoreActions {
  setAuth: (user: UserProfile, tokens: AuthTokens) => void;
  setUser: (user: UserProfile | null) => void;
  logout: () => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

const initialToken = localStorage.getItem(ENV.TOKEN_KEY);

export const useAuthStore = create<AuthState & AuthStoreActions>((set) => ({
  user: null,
  tokens: initialToken ? { access_token: initialToken, token_type: 'bearer' } : null,
  isAuthenticated: !!initialToken,
  isLoading: false,
  error: null,

  setAuth: (user, tokens) => {
    localStorage.setItem(ENV.TOKEN_KEY, tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem(ENV.REFRESH_TOKEN_KEY, tokens.refresh_token);
    }
    set({ user, tokens, isAuthenticated: true, isLoading: false, error: null });
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  logout: () => {
    localStorage.removeItem(ENV.TOKEN_KEY);
    localStorage.removeItem(ENV.REFRESH_TOKEN_KEY);
    set({ user: null, tokens: null, isAuthenticated: false, isLoading: false, error: null });
  },

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
}));
