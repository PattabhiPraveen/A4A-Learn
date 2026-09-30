import { apiRequest } from "./apiClient";

import type {
  AccessibilityProfileUpdate,
  AuthUser,
  LoginRequest,
  LoginResponse,
} from "../types/auth";

export async function login(
  request: LoginRequest,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(
    "/auth/login",
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export async function getCurrentUser(
  token: string,
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/users/me",
    {
      method: "GET",
      token,
    },
  );
}

export async function updateAccessibilityProfile(
  request: AccessibilityProfileUpdate,
  token: string,
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/users/me/accessibility",
    {
      method: "PATCH",
      token,
      body: JSON.stringify(request),
    },
  );
}