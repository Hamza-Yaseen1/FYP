export interface Task {
  id: string;
  description: string;
  deadline: string | null;
  priority_indicator: string | null;
  requires_action: boolean;
  status: string;
  source_message_id: string;
  source_message_preview: string;
  created_at: string;
  updated_at: string | null;
  snoozed_until: string | null;
  is_snoozed: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getTasks(): Promise<Task[]> {
  const response = await fetch(`${API_BASE}/tasks`, {
    credentials: "include",
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Please log in to view your tasks");
    }
    throw new Error("Failed to fetch tasks. Please try again later.");
  }

  return response.json();
}

export async function completeTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/status`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ status: "completed" }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error("Please log in to complete tasks");
    }

    if (response.status === 404) {
      throw new Error("Task not found. It may have already been completed.");
    }

    throw new Error(error.detail || "Failed to complete task. Please try again later.");
  }

  return response.json();
}

export async function snoozeTask(taskId: string, duration: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/snooze`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ duration }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error("Please log in to snooze tasks");
    }

    if (response.status === 404) {
      throw new Error("Task not found. It may have already been completed.");
    }

    throw new Error(error.detail || "Failed to snooze task. Please try again later.");
  }

  return response.json();
}

export interface TaskSourceMessage {
  id: string;
  sender: string;
  content: string;
  source: string;
  created_at: string;
}

export async function getTaskMessage(taskId: string): Promise<TaskSourceMessage> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/message`, {
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    if (response.status === 401) {
      throw new Error("Please log in to view message");
    }

    if (response.status === 404) {
      throw new Error("Task or message not found.");
    }

    throw new Error(error.detail || "Failed to fetch message. Please try again later.");
  }

  return response.json();
}