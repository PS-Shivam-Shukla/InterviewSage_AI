import api from "../../../api/client";

export interface DashboardSummary {
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

export const dashboardService = {

  async getSummary(): Promise<DashboardSummary> {
    const res = await api.get("/analytics/summary");
    return res.data.summary;
  },

  async getTrends(): Promise<TrendItem[]> {
    const res = await api.get("/analytics/trends");
    return res.data.trends;
  },

  async getCompetencies(): Promise<CompetencyItem[]> {
    const res = await api.get("/analytics/competencies");
    return res.data.competencies;
  }

};