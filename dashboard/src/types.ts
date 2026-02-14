// Type definitions for the Intrusive Thoughts Dashboard

export interface Mood {
  id: string;
  name: string;
  emoji: string;
  description: string;
  weights?: Record<string, number>;
}

export interface TodayMood {
  id: string;
  name: string;
  emoji: string;
  description: string;
  drifted_to?: string;
  activity_log?: ActivityLogEntry[];
}

export interface ActivityLogEntry {
  time: string;
  action: {
    from?: string;
    to?: string;
    type?: string;
  };
}

export interface Thought {
  id: string;
  prompt: string;
  weight: number;
  weights: Record<string, number>;
}

export interface ThoughtsData {
  thoughts: Record<string, Thought>;
}

export interface HistoryEntry {
  timestamp: string;
  thought: string;
  thought_id?: string;
  mood?: string;
  summary?: string;
  energy?: string;
  vibe?: string;
  completed?: boolean;
}

export interface PickEntry {
  timestamp: string;
  thought: string;
  today_mood?: string;
  [key: string]: any; // For additional metadata
}

export interface RejectionEntry {
  timestamp: string;
  thought_id: string;
  mood: string;
  reason: string;
  flavor_text: string;
}

export interface StreamItem {
  type: 'pick' | 'rejection' | 'mood_drift' | 'activity';
  timestamp: string;
  thought_id?: string;
  mood?: string;
  summary: string;
  details: any;
}

export interface Achievement {
  name: string;
  description: string;
  tier_emoji?: string;
  points: number;
  earned_at: string;
}

export interface AchievementsData {
  earned: Achievement[];
  total_points: number;
}

export interface AllAchievements {
  achievements: Record<string, any>;
  tiers: Record<string, any>;
}

export interface MoodHistoryEntry {
  date: string;
  mood_id: string;
}

export interface Streaks {
  current_streaks: {
    activity_type?: string[];
    mood?: string[];
    time_of_day?: string[];
  };
}

export interface JournalEntry {
  date: string;
  filename: string;
  content: string;
  preview: string;
  word_count: number;
}

export interface Soundtrack {
  mood_soundtracks: Record<string, {
    vibe_description: string;
    genres: string[];
  }>;
}

export interface PresetData {
  description?: string;
  weights: Record<string, number>;
  [key: string]: any;
}

export interface SchedulePhase {
  time: string;
  phase: string;
}

export interface ScheduleData {
  schedule: SchedulePhase[];
  current_phase: string;
}

export interface NightStats {
  day_picks: number;
  night_picks: number;
  total: number;
  night_percentage: number;
}

export interface IntrospectionData {
  mood_state?: {
    current_mood?: {
      name: string;
      emoji: string;
    };
  };
  memory_state?: {
    health_score: string;
  };
  trust_state?: {
    current_score: string;
  };
  evolution_state?: {
    current_generation: string;
  };
  system_health?: {
    overall_status: string;
  };
  error?: string;
}

export interface SystemExplanation {
  output?: string;
  system?: string;
  error?: string;
  stderr?: string;
}

export interface DecisionTrace {
  output?: string;
  error?: string;
  stderr?: string;
}

export interface MemoryData {
  error?: string;
  total_entries?: number;
  recent_activity?: string;
  [key: string]: any;
}

export interface TrustData {
  error?: string;
  trust_score?: string | number;
  status?: string;
  [key: string]: any;
}

export interface EvolutionData {
  error?: string;
  [key: string]: any;
}

export interface ProactiveData {
  error?: string;
  [key: string]: any;
}

export interface HealthData {
  error?: string;
  [key: string]: any;
}

export interface APIResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  error?: string;
  data?: T;
}

export interface StatsResponse {
  total_picks: number;
  total_completed: number;
  achievements: number;
  points: number;
  thought_counts: Record<string, number>;
  recent: HistoryEntry[];
}

export interface SystemsResponse {
  mood: { status: string; current_mood: TodayMood | null };
  memory: { status: string; entries: number };
  thoughts: { status: string; total_thoughts: number };
  achievements: { status: string; earned: number };
  health: { status: string; monitoring: boolean };
}