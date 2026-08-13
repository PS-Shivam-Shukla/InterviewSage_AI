import { createContext } from 'react';
import { AuthState, LoginResponse } from '../types/auth.types';
import { LoginFormData, RegisterFormData } from '../utils/validationHelpers';

export interface AuthContextType extends AuthState {
  login: (credentials: LoginFormData) => Promise<LoginResponse>;
  register: (data: RegisterFormData) => Promise<LoginResponse>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
