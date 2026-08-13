export interface Resume {
  id: string;
  user_id: string;
  file_path: string;
  raw_text: string;
  parsed_skills: string[];
  parsed_experience: string[];
  seniority_signal: string;
  status?: 'PROCESSING' | 'COMPLETED' | 'FAILED';
  created_at: string;
}

export interface SkillBreakdown {
  technical: string[];
  soft: string[];
  missing: string[];
  all: string[];
}

export interface ExperienceItem {
  id: string;
  title: string;
  company: string;
  period: string;
  description: string;
  highlights: string[];
  technologies: string[];
}

export interface EducationItem {
  id: string;
  degree: string;
  institution: string;
  field_of_study: string;
  graduation_year: string;
  gpa?: string;
}

export interface ProjectItem {
  id: string;
  title: string;
  description: string;
  technologies: string[];
  link?: string;
  role?: string;
}

export interface CertificationItem {
  id: string;
  name: string;
  issuer: string;
  issue_date: string;
  credential_id?: string;
  verified?: boolean;
}

export interface SectionCompleteness {
  contact: number;
  summary: number;
  experience: number;
  education: number;
  skills: number;
  projects: number;
  [key: string]: number;
}

export interface RadarDataPoint {
  subject: string;
  candidateScore: number;
  benchmarkScore: number;
}

export interface SeniorityBreakdownData {
  experience_score: number;
  ownership_score: number;
  architecture_score: number;
  leadership_score: number;
  complexity_score: number;
}

export interface ExperienceMetricsData {
  total_months: number;
  relevant_months: number;
}

export interface ResumeAnalysis {
  resume_id: string;
  file_name: string;
  status?: 'PROCESSING' | 'COMPLETED' | 'FAILED';
  resume_quality_score: number;
  seniority_signal: string;
  seniority_score?: number;
  experience_metrics?: ExperienceMetricsData;
  seniority_breakdown?: SeniorityBreakdownData;
  seniority_evidence?: string[];
  seniority_limitations?: string[];
  skills: SkillBreakdown;
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
  certifications: CertificationItem[];
  summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  section_completeness: SectionCompleteness;
  industry_percentile?: number;
  radar_skills?: RadarDataPoint[];
}

export interface ResumeFilterOptions {
  searchQuery: string;
  seniority: string;
  skillFilter: string;
  sortBy: 'date_desc' | 'date_asc' | 'name_asc' | 'seniority';
  viewMode: 'grid' | 'table';
  selectedIds: string[];
}
