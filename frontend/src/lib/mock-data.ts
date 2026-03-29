import type { ConversationEntry, WellnessSnapshot } from "../types";

export const mockSnapshot: WellnessSnapshot = {
  displayName: "Aarav Sharma",
  email: "aarav.preview@example.com",
  latestMhi: 72,
  category: "Mild Stress",
  checkInsThisWeek: 5,
  streakDays: 12,
  voiceEnabled: true,
  weeklyTrend: [66, 64, 69, 71, 68, 74, 72],
  emotionMix: [
    { label: "Calm", value: 34 },
    { label: "Stress", value: 25 },
    { label: "Hopeful", value: 18 },
    { label: "Anxious", value: 13 },
    { label: "Sad", value: 10 }
  ],
  recentSessions: [
    {
      id: "s1",
      time: "Today, 8:15 PM",
      summary: "Talked about feeling overloaded with deadlines and sleep drift.",
      mood: "Stress",
      mhi: 72
    },
    {
      id: "s2",
      time: "Yesterday, 10:02 PM",
      summary: "Shared anxiety before presentation and practiced reframing thoughts.",
      mood: "Anxious",
      mhi: 69
    },
    {
      id: "s3",
      time: "2 days ago",
      summary: "Discussed family conflict and ways to set boundaries calmly.",
      mood: "Mixed",
      mhi: 74
    }
  ],
  assessment: {
    phq2: 1,
    gad2: 2,
  },
};

export const mockConversation: ConversationEntry[] = [
  {
    id: "a1",
    role: "assistant",
    content:
      "You are in a safe check-in space. Tell me what felt heavy today, and we will break it down together.",
    timestamp: "08:17 PM"
  },
  {
    id: "u1",
    role: "user",
    content:
      "I keep feeling restless and behind. I cannot switch off my thoughts when I try to sleep.",
    timestamp: "08:18 PM"
  },
  {
    id: "a2",
    role: "assistant",
    content:
      "That sounds exhausting. I notice both pressure and mental overactivation there. We can first slow the spiral, then look at what is feeding it.",
    timestamp: "08:18 PM"
  }
];
