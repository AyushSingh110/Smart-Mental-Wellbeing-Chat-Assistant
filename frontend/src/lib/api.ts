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
    avatar_id?: string;
    preferred_language?: string;
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
    avatarId: user.avatar_id ?? "therapist",
    preferredLanguage: user.preferred_language ?? "en",
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
      crisis_tier?: string;
      cbt_technique_suggested?: string;
    }>;
  }>("/user/history?limit=20", { token });

  return payload.conversations.flatMap((item, index) => [
    {
      id: `user-${index}-${item.timestamp}`,
      role: "user" as const,
      content: item.message,
      timestamp: new Date(item.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
    {
      id: `assistant-${index}-${item.timestamp}`,
      role: "assistant" as const,
      content: item.response,
      timestamp: new Date(item.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      mhi: item.mhi,
      category: item.category,
      crisisTier: item.crisis_tier,
      cbtTechniqueSuggested: item.cbt_technique_suggested,
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

// -- Avatar & Profile ----------------------------------------------------------

export async function updateUserProfile(
  token: string,
  data: { avatar_id?: string; preferred_language?: string },
) {
  return request<{ status: string }>("/user/profile", {
    method: "PUT",
    token,
    body: data,
  });
}

export async function getUserProfile(token: string) {
  return request<{
    avatar_id: string;
    preferred_language: string;
    name: string;
    email: string;
    latest_mhi: number;
  }>("/user/profile", { token });
}

export async function avatarSpeak(
  token: string,
  text: string,
  language_code: string,
  avatar_id: string,
  emotion_label = "default",
  crisis_tier = "none",
): Promise<{ audioUrl: string; durationMs: number }> {
  const response = await fetch(`${API_BASE_URL}/avatar/speak`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text, language_code, avatar_id, emotion_label, crisis_tier }),
  });

  if (!response.ok) {
    throw new Error(`Avatar speak failed: ${response.status}`);
  }

  const durationMs = parseInt(response.headers.get("X-Audio-Duration-Ms") ?? "2000", 10);
  const blob = await response.blob();
  return { audioUrl: URL.createObjectURL(blob), durationMs };
}

// -- Voice quota ---------------------------------------------------------------

export async function getVoiceQuota(token: string) {
  return request<{
    chars_used: number;
    chars_limit: number;
    chars_remaining: number;
    api_key_set: boolean;
  }>("/voice/quota", { token });
}

// -- CBT -----------------------------------------------------------------------

export async function recordCBTSession(
  token: string,
  technique: string,
  notes = "",
  completed = false,
) {
  return request<{ status: string; session_id: string }>("/cbt/session", {
    method: "POST",
    token,
    body: { technique, notes, completed },
  });
}

export async function getCBTSessions(token: string) {
  return request<{
    count: number;
    sessions: Array<{
      technique: string;
      started_at: string;
      completed_at?: string;
      notes?: string;
    }>;
  }>("/cbt/sessions", { token });
}

// -- Mood Journal --------------------------------------------------------------

export async function saveMoodEntry(
  token: string,
  mood_rating: number,
  notes = "",
) {
  return request<{ status: string; mood_rating: number }>("/mood/journal", {
    method: "POST",
    token,
    body: { mood_rating, notes },
  });
}

export async function getMoodJournal(token: string) {
  return request<{
    count: number;
    entries: Array<{ timestamp: string; mood_rating: number; notes: string }>;
  }>("/mood/journal", { token });
}

// -- Crisis History ------------------------------------------------------------

export async function getCrisisHistory(token: string) {
  return request<{
    count: number;
    events: Array<{
      timestamp: string;
      crisis_tier: string;
      crisis_score: number;
      message_snippet: string;
    }>;
  }>("/crisis/history", { token });
}

export { API_BASE_URL };
