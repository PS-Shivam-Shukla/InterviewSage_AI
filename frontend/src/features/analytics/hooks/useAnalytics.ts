import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '../../../services/analytics.service';
import {
  AnalyticsSummary,
  TrendItem,
  CompetencyItem,
  VoiceAnalyticsSummary,
} from '../types/analytics.types';

export function useAnalyticsSummary() {
  return useQuery<AnalyticsSummary, Error>({
    queryKey: ['analytics-summary'],
    queryFn: analyticsService.getAnalyticsSummary,
    staleTime: 30000,
  });
}

export function useAnalyticsTrends() {
  return useQuery<TrendItem[], Error>({
    queryKey: ['analytics-trends'],
    queryFn: analyticsService.getAnalyticsTrends,
    staleTime: 30000,
  });
}

export function useAnalyticsCompetencies() {
  return useQuery<CompetencyItem[], Error>({
    queryKey: ['analytics-competencies'],
    queryFn: analyticsService.getAnalyticsCompetencies,
    staleTime: 30000,
  });
}

export function useAnalyticsVoice() {
  return useQuery<VoiceAnalyticsSummary, Error>({
    queryKey: ['analytics-voice'],
    queryFn: analyticsService.getAnalyticsVoice,
    staleTime: 30000,
  });
}
