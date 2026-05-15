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
  avatarId?: string;
  preferredLanguage?: string;
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
  cbtCounts?: Record<string, number>;
  sessionSummary?: {
    totalTurns: number;
    avgMhi: number;
    languagesUsed: string[];
  };
  avatarId?: string;
  preferredLanguage?: string;
};

export type ConversationEntry = {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: string;
  mhi?: number;
  category?: string;
  crisisTier?: string;
  cbtTechniqueSuggested?: string;
  confidence?: number;         // Whisper detection confidence (0-1)
  languageCode?: string;       // detected language code
};

export type ChatApiResponse = {
  response: string;
  emotion_scores: Record<string, number>;
  crisis_score: number;
  crisis_tier: string;
  intent: string;
  mhi: number;
  category: string;
  cbt_technique_suggested?: string | null;
  // Extended fields (Round 2)
  top_3_emotions?: Array<[string, number]>;
  emotion_complexity?: number;
  suppression_flagged?: boolean;
  crisis_velocity?: number;
  behavioral_profile?: {
    overall: number;
    categories: Record<string, number>;
    flagged: string[];
    dominant: string | null;
  };
  pre_voice_alert?: boolean;
  mhi_trajectory?: string;
};

// Avatar

export type AvatarPersona = {
  id: "therapist" | "companion" | "guide" | "elder";
  name: string;
  description: string;
  emoji: string;
  accentColor: string;
  voiceDescription: string;
};

export const AVATAR_PERSONAS: AvatarPersona[] = [
  {
    id: "therapist",
    name: "Dr. Aryan",
    description: "Calm, professional therapist",
    emoji: "\u{1F468}\u200D\u2695\uFE0F",
    accentColor: "#4a84d6",
    voiceDescription: "Warm, measured, reassuring",
  },
  {
    id: "companion",
    name: "Priya",
    description: "Warm, friendly companion",
    emoji: "\u{1F469}",
    accentColor: "#3d8a5c",
    voiceDescription: "Gentle, expressive, caring",
  },
  {
    id: "guide",
    name: "Sage",
    description: "Neutral, gentle guide",
    emoji: "\u{1F9D8}",
    accentColor: "#6a5acd",
    voiceDescription: "Calm, neutral, grounding",
  },
  {
    id: "elder",
    name: "Dada Ji",
    description: "Wise, patient elder figure",
    emoji: "\u{1F9D3}",
    accentColor: "#b5822a",
    voiceDescription: "Deep, patient, experienced",
  },
];

// CBT

export type CBTTechnique = {
  id: string;
  label: string;
  description: string;
  icon: string;
};

export const CBT_TECHNIQUES: CBTTechnique[] = [
  { id: "thought_record",          label: "Thought Record",           description: "Identify automatic thoughts and reframe them", icon: "\u{1F4DD}" },
  { id: "breathing",               label: "Breathing Exercise",       description: "4-7-8 pattern for calm and focus",            icon: "\u{1F4A8}" },
  { id: "grounding",               label: "Grounding (5-4-3-2-1)",    description: "Sensory anchoring for present-moment focus",   icon: "\u{1F33F}" },
  { id: "mood_journal",            label: "Mood Journal",             description: "Daily mood rating with reflection notes",      icon: "\u{1F4D3}" },
  { id: "cognitive_restructuring", label: "Cognitive Restructuring",  description: "Guided reframing of negative thought patterns", icon: "\u{1F9E0}" },
];

export const CBT_LABELS: Record<string, string> = Object.fromEntries(
  CBT_TECHNIQUES.map((t) => [t.id, t.label])
);

// Languages

export type SupportedLanguage = {
  code: string;
  name: string;
  flag: string;
};

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: "en", name: "English",    flag: "\u{1F1EC}\u{1F1E7}" },
  { code: "hi", name: "Hindi",      flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "bn", name: "Bengali",    flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "ta", name: "Tamil",      flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "te", name: "Telugu",     flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "mr", name: "Marathi",    flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "gu", name: "Gujarati",   flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "pa", name: "Punjabi",    flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "kn", name: "Kannada",    flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "ml", name: "Malayalam",  flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "ur", name: "Urdu",       flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "or", name: "Odia",       flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "as", name: "Assamese",   flag: "\u{1F1EE}\u{1F1F3}" },
  { code: "ne", name: "Nepali",     flag: "\u{1F1F3}\u{1F1F5}" },
  { code: "sa", name: "Sanskrit",   flag: "\u{1F1EE}\u{1F1F3}" },
];
