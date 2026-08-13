export type UserRole = 'ADMIN' | 'RECRUITER' | 'CANDIDATE' | 'SUPERVISOR';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified?: boolean;
  avatar_url?: string;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
}

export interface LoginResponse extends AuthTokens {
  user: UserProfile;
}

export interface AuthState {
  user: UserProfile | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
