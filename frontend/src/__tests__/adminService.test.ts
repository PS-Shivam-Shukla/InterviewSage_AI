import { describe, it, expect, vi } from 'vitest';
import { adminService } from '../services/admin.service';
import { apiClient } from '../api/client';

describe('adminService Unit Tests', () => {
  it('should have required service API methods', () => {
    expect(typeof adminService.getDashboardSummary).toBe('function');
    expect(typeof adminService.getLiveInterviews).toBe('function');
    expect(typeof adminService.getInterviewTimeline).toBe('function');
    expect(typeof adminService.getPromptHistory).toBe('function');
    expect(typeof adminService.getCostAnalytics).toBe('function');
    expect(typeof adminService.getReviewQueue).toBe('function');
    expect(typeof adminService.processReviewStatus).toBe('function');
  });

  it('getDashboardSummary should call GET /admin/dashboard', async () => {
    const mockSummary = {
      total_interviews: 12,
      active_interviews: 2,
      completed_interviews: 10,
      failed_interviews: 0,
      success_rate: 100.0,
      avg_interview_duration_minutes: 18.5,
      avg_ai_score: 88.4,
      avg_candidate_score: 78.2,
      total_ai_requests: 48,
      avg_latency_ms: 1200,
      avg_token_usage: 450,
      total_token_cost_usd: 0.125,
      hallucination_rate: 0.01,
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockSummary });

    const result = await adminService.getDashboardSummary();

    expect(spy).toHaveBeenCalledWith('/admin/dashboard');
    expect(result.total_interviews).toBe(12);
    expect(result.active_interviews).toBe(2);
    spy.mockRestore();
  });

  it('getLiveInterviews should call GET /admin/interviews/live', async () => {
    const mockLive = [
      {
        interview_id: 'int-live-1',
        candidate_name: 'Alice Johnson',
        current_round: 'Technical',
        question_number: 3,
        workflow_stage: 'TECHNICAL',
        current_agent: 'TechnicalAgent',
        elapsed_seconds: 450,
        thread_id: 'th-1',
        worker_id: 'worker-01',
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockLive });

    const result = await adminService.getLiveInterviews();

    expect(spy).toHaveBeenCalledWith('/admin/interviews/live');
    expect(result.length).toBe(1);
    expect(result[0].candidate_name).toBe('Alice Johnson');
    spy.mockRestore();
  });

  it('getInterviewTimeline should call GET /admin/interview/:id/timeline', async () => {
    const mockTimeline = {
      interview_id: 'int-1',
      candidate_name: 'Bob Smith',
      job_title: 'Backend Engineer',
      current_stage: 'COMPLETED',
      timeline: [],
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockTimeline });

    const result = await adminService.getInterviewTimeline('int-1');

    expect(spy).toHaveBeenCalledWith('/admin/interview/int-1/timeline');
    expect(result.interview_id).toBe('int-1');
    spy.mockRestore();
  });

  it('getPromptHistory should call GET /admin/prompts/history', async () => {
    const mockPrompts = [
      {
        prompt_key: 'EVALUATION_SYSTEM_PROMPT',
        version: '1.2',
        description: 'Per-turn evaluation reasoning prompt',
        is_active: true,
        variables: ['candidate_answer', 'question_text'],
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockPrompts });

    const result = await adminService.getPromptHistory();

    expect(spy).toHaveBeenCalledWith('/admin/prompts/history');
    expect(result.length).toBe(1);
    expect(result[0].prompt_key).toBe('EVALUATION_SYSTEM_PROMPT');
    spy.mockRestore();
  });

  it('getCostAnalytics should call GET /admin/analytics/costs', async () => {
    const mockCost = {
      today_usd: 0.05,
      this_week_usd: 0.25,
      this_month_usd: 1.12,
      total_tokens_consumed: 150000,
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockCost });

    const result = await adminService.getCostAnalytics();

    expect(spy).toHaveBeenCalledWith('/admin/analytics/costs');
    expect(result.today_usd).toBe(0.05);
    spy.mockRestore();
  });

  it('getReviewQueue should call GET /admin/review/queue', async () => {
    const mockQueue = [
      {
        review_id: 'rev-1',
        interview_id: 'int-1',
        confidence: 0.55,
        reason: 'Low confidence technical score evaluation',
        status: 'PENDING',
        created_at: '2026-08-08T12:00:00Z',
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockQueue });

    const result = await adminService.getReviewQueue();

    expect(spy).toHaveBeenCalledWith('/admin/review/queue', { params: {} });
    expect(result.length).toBe(1);
    expect(result[0].confidence).toBe(0.55);
    spy.mockRestore();
  });

  it('processReviewStatus should call POST /admin/review/:id/status?status=APPROVED', async () => {
    const mockRes = { message: 'Review item updated successfully', status: 'APPROVED' };
    const spy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockRes });

    const result = await adminService.processReviewStatus('rev-1', 'APPROVED');

    expect(spy).toHaveBeenCalledWith('/admin/review/rev-1/status', null, { params: { status: 'APPROVED' } });
    expect(result.status).toBe('APPROVED');
    spy.mockRestore();
  });
});
