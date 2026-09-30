export type AccessibilityProfile =
  | "standard"
  | "deaf"
  | "hard_of_hearing"
  | "non_speaking";

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
  accessibility_profile: AccessibilityProfile;
  preferred_language: string;
  isl_enabled: boolean;
  captions_enabled: boolean;
  is_active: boolean;
}

export interface AccessibilityProfileUpdate {
  accessibility_profile: AccessibilityProfile;
  preferred_language: string;
  isl_enabled: boolean;
  captions_enabled: boolean;
}