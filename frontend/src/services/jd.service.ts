import { apiClient } from '../api/client';

export interface JobDescriptionCreatePayload {
  raw_text: string;
  target_role: string;
  company_name?: string;
  industry?: string;
}

export interface JobDescriptionResponse {
  id: string;
  user_id: string;
  raw_text: string;
  target_role: string;
  company_name: string | null;
  industry: string | null;
  required_skills: string[];
  seniority_level: string;
  created_at: string;
}

export interface JobDescriptionMatchResponse {
  jd_id: string;
  resume_id: string;
  target_role: string;
  company_name: string | null;
  candidate_seniority: string;
  required_seniority: string;
  ats_score: number;
  matched_skills: string[];
  missing_skills: string[];
  resume_skill_count: number;
  jd_skill_count: number;
}

export const jdService = {
  async createJobDescription(payload: JobDescriptionCreatePayload): Promise<JobDescriptionResponse> {
    const response = await apiClient.post<JobDescriptionResponse>('/job-descriptions/', payload, {
      timeout: 120000,
    });
    return response.data;
  },

  async getJobDescription(id: string): Promise<JobDescriptionResponse> {
    const response = await apiClient.get<JobDescriptionResponse>(`/job-descriptions/${id}`);
    return response.data;
  },

  async listJobDescriptions(): Promise<JobDescriptionResponse[]> {
    const response = await apiClient.get<JobDescriptionResponse[]>('/job-descriptions/');
    return response.data;
  },

  async matchResumeWithJd(jdId: string, resumeId: string): Promise<JobDescriptionMatchResponse> {
    const response = await apiClient.post<JobDescriptionMatchResponse>(`/job-descriptions/${jdId}/match/${resumeId}`);
    return response.data;
  },
};
