import { describe, it, expect, vi } from 'vitest';
import { reportService } from '../services/report.service';
import { apiClient } from '../api/client';

describe('reportService Unit Tests', () => {
  it('should have required service API methods', () => {
    expect(typeof reportService.getInterviewReport).toBe('function');
    expect(typeof reportService.getReportHistory).toBe('function');
    expect(typeof reportService.downloadInterviewReportPdf).toBe('function');
  });

  it('getInterviewReport should call GET /reports/:interviewId', async () => {
    const mockReport = {
      interview_id: 'int-123',
      status: 'COMPLETED',
      overall_score: 88,
      role: 'Senior Python Engineer',
      competency_scorecard: [{ competency: 'Backend Architecture', score: 90, fullMark: 100 }],
      improvement_plan: [{ id: '1', topic: 'Concurrency', description: 'Study lock-free data structures', targetSkill: 'Python', priority: 'High' }],
      transcript_snapshot: [{ question: 'What is GIL?', answer: 'Global Interpreter Lock', score: 90, reasoning: 'Accurate' }],
      generated_at: '2026-08-08T12:00:00Z',
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockReport });

    const result = await reportService.getInterviewReport('int-123');

    expect(spy).toHaveBeenCalledWith('/reports/int-123');
    expect(result.interview_id).toBe('int-123');
    expect(result.overall_score).toBe(88);
    expect(result.competency_scorecard.length).toBe(1);
    spy.mockRestore();
  });

  it('getReportHistory should call GET /reports/user/history', async () => {
    const mockHistory = [
      {
        interview_id: 'int-123',
        role: 'Python Developer',
        status: 'COMPLETED',
        overall_score: 85,
        generated_at: '2026-08-08T12:00:00Z',
        total_questions: 5,
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockHistory });

    const result = await reportService.getReportHistory();

    expect(spy).toHaveBeenCalledWith('/reports/user/history');
    expect(result.length).toBe(1);
    expect(result[0].overall_score).toBe(85);
    spy.mockRestore();
  });

  it('downloadInterviewReportPdf should call GET /reports/:id/pdf with blob responseType', async () => {
    const mockBlob = new Blob(['%PDF-1.4 mock content'], { type: 'application/pdf' });
    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockBlob });

    const result = await reportService.downloadInterviewReportPdf('int-123');

    expect(spy).toHaveBeenCalledWith('/reports/int-123/pdf', { responseType: 'blob' });
    expect(result).toBeInstanceOf(Blob);
    spy.mockRestore();
  });
});
