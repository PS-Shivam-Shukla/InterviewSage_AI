export interface CandidateProfile {
  id: string;
  candidate_id: string;
  experience_years: number;
  skills: string[];
  current_level: string;
  strengths: string[];
  weaknesses: string[];
  summary?: string | null;
  updated_at: string;
}

export interface CandidateMemory {
  id: string;
  candidate_id: string;
  interview_id?: string | null;
  memory_type: string;
  summary: string;
  key_topics: string[];
  created_at: string;
}

export interface SkillProgress {
  id: string;
  candidate_id: string;
  skill_name: string;
  current_score: number;
  best_score: number;
  average_score: number;
  trend: 'IMPROVING' | 'REGRESSING' | 'STABLE' | string;
  total_evaluations: number;
  updated_at: string;
}

export interface LearningRecommendation {
  id: string;
  candidate_id: string;
  interview_id?: string | null;
  target_topic: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  suggested_action: string;
  week_number: number;
  created_at: string;
}

export interface MemorySummary {
  id: string;
  candidate_id: string;
  compressed_summary: string;
  interview_count_covered: number;
  key_strengths: string[];
  key_weaknesses: string[];
  created_at: string;
}

export interface CandidateTimelineItem {
  interview_id: string;
  date: string;
  overall_score?: number | null;
  summary: string;
  key_topics: string[];
}
