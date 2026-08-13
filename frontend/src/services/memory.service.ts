import { apiClient } from '../api/client';
import {
  CandidateProfile,
  CandidateMemory,
  SkillProgress,
  LearningRecommendation,
  MemorySummary,
  CandidateTimelineItem,
} from '../features/memory/types/memory.types';

export const memoryService = {
  async getCandidateProfile(candidateId: string): Promise<CandidateProfile> {
    const res = await apiClient.get<CandidateProfile>(`/memory/${candidateId}`);
    return res.data;
  },

  async saveCandidateMemory(
    candidateId: string,
    payload: { summary: string; key_topics?: string[]; memory_type?: string; interview_id?: string }
  ): Promise<CandidateMemory> {
    const res = await apiClient.post<CandidateMemory>(`/memory/${candidateId}`, payload);
    return res.data;
  },

  async getCandidateTimeline(candidateId: string): Promise<CandidateTimelineItem[]> {
    const res = await apiClient.get<CandidateTimelineItem[]>(`/memory/${candidateId}/timeline`);
    return res.data;
  },

  async getSkillProgression(candidateId: string): Promise<SkillProgress[]> {
    const res = await apiClient.get<SkillProgress[]>(`/memory/${candidateId}/skills`);
    return res.data;
  },

  async getLearningRecommendations(candidateId: string): Promise<LearningRecommendation[]> {
    const res = await apiClient.get<LearningRecommendation[]>(`/memory/${candidateId}/recommendations`);
    return res.data;
  },

  async compressMemories(candidateId: string): Promise<MemorySummary> {
    const res = await apiClient.post<MemorySummary>(`/memory/${candidateId}/summarize`);
    return res.data;
  },
};
