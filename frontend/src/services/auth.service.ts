import { apiClient } from '../api/client';
import { LoginResponse, UserProfile } from '../types/auth.types';
import { LoginFormData, RegisterFormData } from '../utils/validationHelpers';

export const authService = {
  async login(credentials: LoginFormData): Promise<LoginResponse> {
    const payload = {
      email: credentials.email,
      password: credentials.password,
    };

    console.log("LOGIN URL", apiClient.defaults.baseURL);
    console.log("LOGIN PAYLOAD", payload);

    const response = await apiClient.post<LoginResponse>('/auth/login', payload);
    return response.data;
  },

  async register(data: RegisterFormData): Promise<LoginResponse> {
    const payload = {
      email: data.email,
      password: data.password,
      full_name: data.full_name,
    };

    console.log("REGISTER URL", apiClient.defaults.baseURL);
    console.log("REGISTER PAYLOAD", payload);

    const response = await apiClient.post<LoginResponse>('/auth/register', payload);
    return response.data;
  },

  async getCurrentUser(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>('/auth/me');
    return response.data;
  },
};
