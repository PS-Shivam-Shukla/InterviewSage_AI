import { describe, it, expect, vi } from 'vitest';
import { analyticsService } from '../services/analytics.service';
import { apiClient } from '../api/client';

describe('analyticsService Unit Tests', () => {
  it('should have required service API methods', () => {
    expect(typeof analyticsService.getAnalyticsSummary).toBe('function');
    expect(typeof analyticsService.getAnalyticsTrends).toBe('function');
    expect(typeof analyticsService.getAnalyticsCompetencies).toBe('function');
    expect(typeof analyticsService.getAnalyticsVoice).toBe('function');
  });

  it('getAnalyticsSummary should call GET /analytics/summary', async () => {
    const mockSummary = {
      total_interviews: 5,
      average_score: 84.5,
      completion_rate: 1.0,
      in_progress_count: 0,
      weak_competencies: ['Concurrency'],
      score_trend: [{ date: 'Aug 08', score: 85 }],
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: { summary: mockSummary } });

    const result = await analyticsService.getAnalyticsSummary();

    expect(spy).toHaveBeenCalledWith('/analytics/summary');
    expect(result.total_interviews).toBe(5);
    expect(result.average_score).toBe(84.5);
    spy.mockRestore();
  });

  it('getAnalyticsTrends should call GET /analytics/trends', async () => {
    const mockTrends = [{ interview_id: 'int-1', date: '2026-08-08', score: 90 }];
    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: { trends: mockTrends } });

    const result = await analyticsService.getAnalyticsTrends();

    expect(spy).toHaveBeenCalledWith('/analytics/trends');
    expect(result.length).toBe(1);
    expect(result[0].score).toBe(90);
    spy.mockRestore();
  });

  it('getAnalyticsCompetencies should call GET /analytics/competencies', async () => {
    const mockComp = [{ competency: 'Python', avg_score: 92.0, interview_count: 3 }];
    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: { competencies: mockComp } });

    const result = await analyticsService.getAnalyticsCompetencies();

    expect(spy).toHaveBeenCalledWith('/analytics/competencies');
    expect(result.length).toBe(1);
    expect(result[0].competency).toBe('Python');
    spy.mockRestore();
  });

  it('getAnalyticsVoice should call GET /analytics/voice', async () => {
    const mockVoice = {
      has_voice_data: true,
      voice_sessions_count: 2,
      avg_speaking_speed_wpm: 142.5,
      total_speaking_time_seconds: 240.0,
      total_silence_duration_seconds: 12.0,
      avg_answer_latency_seconds: 1.4,
      total_words_spoken: 600,
      avg_communication_score: 88.0,
      avg_technical_score: 85.0,
      avg_confidence_estimate: 87.0,
    };
    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: { voice: mockVoice } });

    const result = await analyticsService.getAnalyticsVoice();

    expect(spy).toHaveBeenCalledWith('/analytics/voice');
    expect(result.has_voice_data).toBe(true);
    expect(result.avg_speaking_speed_wpm).toBe(142.5);
    spy.mockRestore();
  });
});
