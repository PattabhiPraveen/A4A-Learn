import {
  apiRequest,
} from "./apiClient";

import type {
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