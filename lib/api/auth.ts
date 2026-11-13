import { apiFetch } from "@/lib/api";

export interface AuthMessageResponse {
  message: string;
}

export function forgotPassword(email: string): Promise<AuthMessageResponse> {
  return apiFetch<AuthMessageResponse>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(
  token: string,
  password: string
): Promise<AuthMessageResponse> {
  return apiFetch<AuthMessageResponse>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}
