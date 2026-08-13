import { describe, it, expect, vi } from 'vitest';
import { memoryService } from '../services/memory.service';
import { apiClient } from '../api/client';

describe('memoryService Unit Tests', () => {
  it('should have required service API methods', () => {
    expect(typeof memoryService.getCandidateProfile).toBe('function');
    expect(typeof memoryService.getCandidateTimeline).toBe('function');
    expect(typeof memoryService.getSkillProgression).toBe('function');
    expect(typeof memoryService.getLearningRecommendations).toBe('function');
    expect(typeof memoryService.compressMemories).toBe('function');
  });

  it('getCandidateProfile should call GET /memory/:candidateId', async () => {
    const mockProfile = {
      id: 'prof-1',
      candidate_id: 'user-123',
      experience_years: 5,
      skills: ['Python', 'FastAPI'],
      current_level: 'SENIOR',
      strengths: ['Backend Architecture'],
      weaknesses: ['Frontend CSS'],
      summary: 'Experienced backend developer.',
      updated_at: '2026-08-08T12:00:00Z',
    };

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockProfile });

    const result = await memoryService.getCandidateProfile('user-123');

    expect(spy).toHaveBeenCalledWith('/memory/user-123');
    expect(result.candidate_id).toBe('user-123');
    expect(result.skills.length).toBe(2);
    spy.mockRestore();
  });

  it('getCandidateTimeline should call GET /memory/:candidateId/timeline', async () => {
    const mockTimeline = [
      {
        interview_id: 'int-1',
        date: '2026-08-08',
        overall_score: 88,
        summary: 'Strong backend concurrency performance',
        key_topics: ['Python', 'Asyncio'],
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockTimeline });

    const result = await memoryService.getCandidateTimeline('user-123');

    expect(spy).toHaveBeenCalledWith('/memory/user-123/timeline');
    expect(result.length).toBe(1);
    expect(result[0].overall_score).toBe(88);
    spy.mockRestore();
  });

  it('getSkillProgression should call GET /memory/:candidateId/skills', async () => {
    const mockSkills = [
      {
        id: 'sk-1',
        candidate_id: 'user-123',
        skill_name: 'FastAPI',
        current_score: 90,
        best_score: 95,
        average_score: 88,
        trend: 'IMPROVING',
        total_evaluations: 4,
        updated_at: '2026-08-08T12:00:00Z',
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockSkills });

    const result = await memoryService.getSkillProgression('user-123');

    expect(spy).toHaveBeenCalledWith('/memory/user-123/skills');
    expect(result.length).toBe(1);
    expect(result[0].skill_name).toBe('FastAPI');
    spy.mockRestore();
  });

  it('getLearningRecommendations should call GET /memory/:candidateId/recommendations', async () => {
    const mockRecs = [
      {
        id: 'rec-1',
        candidate_id: 'user-123',
        target_topic: 'Database Sharding',
        priority: 'HIGH',
        suggested_action: 'Study horizontal partition locking strategies',
        week_number: 1,
        created_at: '2026-08-08T12:00:00Z',
      },
    ];

    const spy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({ data: mockRecs });

    const result = await memoryService.getLearningRecommendations('user-123');

    expect(spy).toHaveBeenCalledWith('/memory/user-123/recommendations');
    expect(result.length).toBe(1);
    expect(result[0].priority).toBe('HIGH');
    spy.mockRestore();
  });

  it('compressMemories should call POST /memory/:candidateId/summarize', async () => {
    const mockSummary = {
      id: 'sum-1',
      candidate_id: 'user-123',
      compressed_summary: 'Overall strong technical execution with high system design awareness.',
      interview_count_covered: 3,
      key_strengths: ['Python', 'Concurrency'],
      key_weaknesses: ['Locking'],
      created_at: '2026-08-08T12:00:00Z',
    };

    const spy = vi.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: mockSummary });

    const result = await memoryService.compressMemories('user-123');

    expect(spy).toHaveBeenCalledWith('/memory/user-123/summarize');
    expect(result.interview_count_covered).toBe(3);
    spy.mockRestore();
  });
});
