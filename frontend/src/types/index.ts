export type NavItem = {
  label: string;
  path: string;
  description: string;
};

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  avatar: string;
  picture?: string;
  latestMhi: number;
  phq2: number;
  gad2: number;
};

export type WellnessSnapshot = {
  displayName: string;
  email: string;
  latestMhi: number;
  category: string;
  checkInsThisWeek: number;
  streakDays: number;
  voiceEnabled: boolean;
  weeklyTrend: number[];
  emotionMix: Array<{ label: string; value: number }>;
  recentSessions: Array<{
    id: string;
    time: string;
    summary: string;
    mood: string;
    mhi: number;
  }>;
  assessment: {
    phq2: number;
    gad2: number;
  };
};

export type ConversationEntry = {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: string;
};

export type ChatApiResponse = {
  response: string;
  emotion_scores: Record<string, number>;
  crisis_score: number;
  crisis_tier: string;
  intent: string;
  mhi: number;
  category: string;
};
