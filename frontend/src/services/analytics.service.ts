import { apiClient } from '../api/client';
import {
  AnalyticsSummary,
  TrendItem,
  CompetencyItem,
  VoiceAnalyticsSummary,
} from '../features/analytics/types/analytics.types';

export const analyticsService = {
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const res = await apiClient.get<{ summary: AnalyticsSummary }>('/analytics/summary');
    return res.data.summary;
  },

  async getAnalyticsTrends(): Promise<TrendItem[]> {
    const res = await apiClient.get<{ trends: TrendItem[] }>('/analytics/trends');
    return res.data.trends;
  },

  async getAnalyticsCompetencies(): Promise<CompetencyItem[]> {
    const res = await apiClient.get<{ competencies: CompetencyItem[] }>('/analytics/competencies');
    return res.data.competencies;
  },

  async getAnalyticsVoice(): Promise<VoiceAnalyticsSummary> {
    const res = await apiClient.get<{ voice: VoiceAnalyticsSummary }>('/analytics/voice');
    return res.data.voice;
  },
};
