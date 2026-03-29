import type {
  AuthUser,
  ChatApiResponse,
  ConversationEntry,
  WellnessSnapshot,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type RequestOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
  headers?: Record<string, string>;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      ...(options.headers ?? {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    let detail = fallback;
    try {
      const data = await response.json();
      detail = data.detail ?? fallback;
    } catch {
      detail = fallback;
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function loginWithGoogle(credential: string) {
  return request<{ access_token: string; token_type: string }>("/auth/google", {
    method: "POST",
    body: { credential },
  });
}

export async function getCurrentUser(token: string): Promise<AuthUser> {
  const user = await request<{
    id: string;
    email: string;
    name?: string;
    picture?: string;
    latest_mhi?: number;
    baseline_mhi: number;
    phq2_total: number;
    gad2_total: number;
  }>("/auth/me", { token });

  return {
    id: user.id,
    name: user.name || user.email.split("@")[0],
    email: user.email,
    avatar: user.name
      ? user.name
          .split(" ")
          .map((part) => part[0])
          .join("")
          .slice(0, 2)
          .toUpperCase()
      : user.email.slice(0, 2).toUpperCase(),
    picture: user.picture,
    latestMhi: user.latest_mhi ?? user.baseline_mhi,
    phq2: user.phq2_total,
    gad2: user.gad2_total,
  };
}

export async function getDashboardSnapshot(token: string): Promise<WellnessSnapshot> {
  return request<WellnessSnapshot>("/user/dashboard-summary", { token });
}

export async function getConversationHistory(token: string): Promise<ConversationEntry[]> {
  const payload = await request<{
    count: number;
    conversations: Array<{
      timestamp: string;
      message: string;
      response: string;
      mhi: number;
      category: string;
    }>;
  }>("/user/history?limit=20", { token });

  return payload.conversations.flatMap((item, index) => [
    {
      id: `user-${index}-${item.timestamp}`,
      role: "user",
      content: item.message,
      timestamp: new Date(item.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
    {
      id: `assistant-${index}-${item.timestamp}`,
      role: "assistant",
      content: item.response,
      timestamp: new Date(item.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
  ]);
}

export async function sendChatMessage(
  token: string,
  message: string,
  language_code = "en",
): Promise<ChatApiResponse> {
  return request<ChatApiResponse>("/chat", {
    method: "POST",
    token,
    body: {
      message,
      language_code,
      source: "text",
    },
  });
}

export async function submitAssessment(
  token: string,
  phq2: number,
  gad2: number,
): Promise<{
  status: string;
  phq2: number;
  gad2: number;
  screening_score: number;
}> {
  return request("/assessment", {
    method: "POST",
    token,
    body: { phq2, gad2 },
  });
}

export { API_BASE_URL };
