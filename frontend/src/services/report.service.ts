import { apiClient } from '../api/client';

export interface CompetencyScoreItem {
  competency: string;
  score: number;
  fullMark: number;
}

export interface ImprovementPlanItem {
  id: string;
  topic: string;
  description: string;
  targetSkill: string;
  priority: string;
}

export interface TranscriptSnapshotItem {
  question: string;
  answer: string;
  score: number;
  reasoning: string;
}

export interface InterviewReportResponse {
  interview_id: string;
  status: string;
  overall_score: number;
  role: string;
  competency_scorecard: CompetencyScoreItem[];
  improvement_plan: ImprovementPlanItem[];
  transcript_snapshot: TranscriptSnapshotItem[];
  generated_at: string;
}

export interface ReportHistoryItem {
  interview_id: string;
  role: string;
  status: string;
  overall_score: number;
  generated_at: string;
  completed_at?: string;
  total_questions: number;
}

export const reportService = {
  async getInterviewReport(interviewId: string): Promise<InterviewReportResponse> {
    const response = await apiClient.get<InterviewReportResponse>(`/reports/${interviewId}`);
    return response.data;
  },

  async getReportHistory(): Promise<ReportHistoryItem[]> {
    const response = await apiClient.get<ReportHistoryItem[]>('/reports/user/history');
    return response.data;
  },

  async downloadInterviewReportPdf(interviewId: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(`/reports/${interviewId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
