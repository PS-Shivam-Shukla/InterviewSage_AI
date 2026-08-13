export interface AnalyticsSummary {
  total_interviews: number;
  average_score: number | null;
  completion_rate: number;
  in_progress_count: number;
  weak_competencies: string[];
  score_trend: {
    date: string;
    score: number;
  }[];
}

export interface TrendItem {
  interview_id: string;
  date: string;
  score: number;
}

export interface CompetencyItem {
  competency: string;
  avg_score: number;
  interview_count: number;
}

export interface VoiceAnalyticsSummary {
  has_voice_data: boolean;
  voice_sessions_count: number;
  avg_speaking_speed_wpm?: number;
  total_speaking_time_seconds?: number;
  total_silence_duration_seconds?: number;
  avg_answer_latency_seconds?: number;
  total_words_spoken?: number;
  avg_communication_score?: number;
  avg_technical_score?: number;
  avg_confidence_estimate?: number;
}
