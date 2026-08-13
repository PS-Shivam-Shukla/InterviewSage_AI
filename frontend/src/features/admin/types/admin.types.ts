export interface AdminDashboardSummary {
  total_interviews: number;
  active_interviews: number;
  completed_interviews: number;
  failed_interviews: number;
  success_rate: number;
  avg_interview_duration_minutes: number;
  avg_ai_score: number;
  avg_candidate_score: number;
  total_ai_requests: number;
  avg_latency_ms: number;
  avg_token_usage: number;
  total_token_cost_usd: number;
  hallucination_rate: number;
}

export interface LiveInterviewItem {
  interview_id: string;
  candidate_name: string;
  current_round: string;
  question_number: number;
  workflow_stage: string;
  current_agent: string;
  elapsed_seconds: number;
  thread_id: string;
  worker_id: string;
}

export interface TimelineStep {
  step_number: number;
  event_type: 'QUESTION' | 'ANSWER' | 'EVALUATION' | 'AGENT_LOG' | 'CHECKPOINT' | string;
  timestamp?: string | null;
  question_text?: string | null;
  candidate_answer?: string | null;
  score?: number | null;
  reasoning?: string | null;
  next_agent?: string | null;
  checkpoint_id?: string | null;
}

export interface InterviewTimeline {
  interview_id: string;
  candidate_name: string;
  job_title: string;
  current_stage: string;
  timeline: TimelineStep[];
}

export interface PromptHistoryItem {
  prompt_key: string;
  version: string;
  created_at?: string | null;
  description: string;
  is_active: boolean;
  variables: string[];
}

export type ReviewStatus = 'APPROVED' | 'REJECTED' | 'FLAGGED' | 'OVERRIDDEN';

export interface ReviewQueueItem {
  review_id: string;
  interview_id: string;
  response_id?: string | null;
  confidence: number;
  reason: string;
  assigned_admin?: string | null;
  status: ReviewStatus | string;
  created_at: string;
}

export interface CostAnalytics {
  today_usd: number;
  this_week_usd: number;
  this_month_usd: number;
  by_model?: Record<string, number>;
  by_agent?: Record<string, number>;
  total_tokens_consumed?: number;
}
