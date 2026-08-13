// Base types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface ApiError {
  message: string
  detail?: string
  errors?: Record<string, string[]>
}

// User & Auth types
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'candidate' | 'recruiter' | 'admin'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
  user?: User
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  full_name?: string
  role?: 'candidate' | 'recruiter'
}

// Interview types
export interface Interview {
  id: string
  title: string
  type: 'technical' | 'hr' | 'behavioral'
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
  candidate_id: string
  recruiter_id?: string
  job_description_id?: string
  scheduled_at: string
  duration_minutes: number
  created_at: string
  updated_at: string
}

export interface InterviewQuestion {
  id: string
  interview_id: string
  question_text: string
  question_type: 'technical' | 'behavioral' | 'situational'
  difficulty: 'easy' | 'medium' | 'hard'
  expected_answer?: string
  order_index: number
  created_at: string
}

export interface InterviewAnswer {
  id: string
  interview_id: string
  question_id: string
  answer_text: string
  audio_url?: string
  video_url?: string
  score?: number
  feedback?: string
  created_at: string
}

// Job Description types
export interface JobDescription {
  id: string
  title: string
  company: string
  description: string
  requirements: string[]
  skills: string[]
  experience_level: 'entry' | 'mid' | 'senior' | 'lead'
  employment_type: 'full_time' | 'part_time' | 'contract' | 'freelance'
  location?: string
  salary_range?: {
    min: number
    max: number
    currency: string
  }
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
}

// Resume types
export interface Resume {
  id: string
  user_id: string
  filename: string
  file_url: string
  extracted_text?: string
  skills: string[]
  experience_years?: number
  education: Education[]
  work_experience: WorkExperience[]
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface Education {
  degree: string
  institution: string
  field_of_study?: string
  graduation_year?: number
}

export interface WorkExperience {
  title: string
  company: string
  duration: string
  description?: string
  start_date?: string
  end_date?: string
}

// Report types
export interface Report {
  id: string
  interview_id: string
  candidate_id: string
  overall_score: number
  technical_score?: number
  communication_score?: number
  problem_solving_score?: number
  feedback: string
  recommendations: string[]
  strengths: string[]
  areas_for_improvement: string[]
  decision: 'hire' | 'no_hire' | 'maybe'
  generated_by: string
  created_at: string
  updated_at: string
}

// Analytics types
export interface DashboardSummary {
  total_interviews: number
  interviews_this_month: number
  interviews_this_week: number
  average_score: number
  completion_rate: number
  top_skills: Array<{
    skill: string
    count: number
  }>
  recent_interviews: Interview[]
}

export interface AnalyticsOverview {
  interview_trends: Array<{
    date: string
    count: number
  }>
  score_distribution: Array<{
    range: string
    count: number
  }>
  popular_skills: Array<{
    skill: string
    demand: number
    avg_score: number
  }>
  performance_metrics: {
    avg_interview_duration: number
    candidate_satisfaction: number
    interviewer_efficiency: number
  }
}

// Filter types
export interface InterviewFilters {
  status?: Interview['status']
  type?: Interview['type']
  date_from?: string
  date_to?: string
  candidate_id?: string
  recruiter_id?: string
}

export interface ReportFilters {
  decision?: Report['decision']
  score_min?: number
  score_max?: number
  date_from?: string
  date_to?: string
  candidate_id?: string
}

export interface UserFilters {
  role?: User['role']
  is_active?: boolean
  search?: string
}