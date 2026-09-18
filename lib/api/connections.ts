export interface Connection {
  id: string;
  provider: "whatsapp" | "gmail" | "linkedin";
  status: "connected" | "disconnected" | "error" | "coming_soon";
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

import { clearCache } from "@/lib/api";

export async function getConnections(): Promise<Connection[]> {
  const response = await fetch(`${API_BASE}/connections`, {
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Please log in to view your connections");
    }
    throw new Error("Failed to fetch connections. Please try again later.");
  }

  const data = await response.json();
  return data.connections;
}

export async function createConnection(
  provider: "whatsapp" | "gmail"
): Promise<Connection> {
  const response = await fetch(`${API_BASE}/connections`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ provider }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error("Please log in to connect an account");
    }

    if (response.status === 400) {
      throw new Error(error.detail || "This account is already connected");
    }

    throw new Error(error.detail || "Failed to connect account. Please try again later.");
  }

  clearCache();
  return response.json();
}

export async function deleteConnection(connectionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/connections/${connectionId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error("Please log in to disconnect an account");
    }

    if (response.status === 404) {
      throw new Error("Connection not found. It may have been already disconnected.");
    }

    throw new Error(error.detail || "Failed to disconnect account. Please try again later.");
  }

  clearCache();
}

export async function getGmailAuthUrl(): Promise<string> {
  const response = await fetch(`${API_BASE}/connections/gmail/auth-url`, {
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 401) {
      throw new Error("Please log in to connect Gmail.");
    }
    throw new Error(error.detail || "Failed to start Gmail connect. Please try again.");
  }

  const data = await response.json();
  return data.auth_url;
}
