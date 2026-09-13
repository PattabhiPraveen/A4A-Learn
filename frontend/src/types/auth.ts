export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type?: string;
}

export interface AuthUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}