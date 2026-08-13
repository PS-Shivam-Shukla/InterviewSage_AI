export type InterviewMode = 'VOICE' | 'TEXT' | 'HYBRID';
export type InterviewDifficulty = 'EASY' | 'MEDIUM' | 'HARD' | 'ADAPTIVE';
export type AIState = 'IDLE' | 'THINKING' | 'LISTENING' | 'SPEAKING';

export interface InterviewQuestion {
  id: string;
  text: string;
  category: string;
  difficulty: string;
  competency_focus?: string;
  expected_skills?: string[];
}

export interface InterviewPlan {
  id: string;
  interview_id: string;
  blueprint: {
    total_questions: number;
    target_role: string;
    target_company: string;
    questions: InterviewQuestion[];
  };
  approved: boolean;
}

export interface Interview {
  id: string;
  user_id: string;
  status: 'PLANNING' | 'READY' | 'IN_PROGRESS' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'PENDING';
  current_question_index: number;
  total_questions: number;
  target_role: string;
  target_company: string;
  interview_mode: InterviewMode;
  difficulty: InterviewDifficulty;
  current_question?: InterviewQuestion;
  created_at: string;
  updated_at: string;
}

export interface TranscriptEntry {
  id: string;
  speaker: 'AI' | 'CANDIDATE' | 'SYSTEM';
  text: string;
  timestamp: string;
  audio_url?: string;
  feedback?: {
    technical_score?: number;
    communication_score?: number;
    confidence_score?: number;
    wpm?: number;
    silence_seconds?: number;
  };
}

export interface LiveInterviewMetrics {
  wpm: number;
  silenceSeconds: number;
  latencyMs: number;
  speechQualityScore: number;
  answerQualityScore: number;
  technicalScore: number;
  communicationScore: number;
  confidenceScore: number;
  currentDifficulty: InterviewDifficulty;
  currentCompetency: string;
  timeElapsedSeconds: number;
}

export interface InterviewReplayItem {
  id: string;
  question_text: string;
  candidate_answer: string;
  ai_comment: string;
  technical_score: number;
  communication_score: number;
  strengths: string[];
  weaknesses: string[];
}

export interface CreateInterviewPayload {
  resume_id?: string;
  jd_id?: string;
  target_company?: string;
  target_role?: string;
  interview_mode?: InterviewMode;
  difficulty?: InterviewDifficulty;
  language?: string;
  voice_name?: string;
}

export interface SubmitAnswerPayload {
  interview_id: string;
  question_id: string;
  question_text: string;
  answer: string;
}
