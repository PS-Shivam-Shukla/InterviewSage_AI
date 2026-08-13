import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { memoryService } from '../../../services/memory.service';
import {
  CandidateProfile,
  CandidateTimelineItem,
  SkillProgress,
  LearningRecommendation,
  MemorySummary,
} from '../types/memory.types';

export function useCandidateProfile(candidateId?: string) {
  return useQuery<CandidateProfile, Error>({
    queryKey: ['candidate-profile', candidateId],
    queryFn: () => {
      if (!candidateId) throw new Error('Candidate ID is required');
      return memoryService.getCandidateProfile(candidateId);
    },
    enabled: !!candidateId,
    staleTime: 30000,
  });
}

export function useCandidateTimeline(candidateId?: string) {
  return useQuery<CandidateTimelineItem[], Error>({
    queryKey: ['candidate-timeline', candidateId],
    queryFn: () => {
      if (!candidateId) throw new Error('Candidate ID is required');
      return memoryService.getCandidateTimeline(candidateId);
    },
    enabled: !!candidateId,
    staleTime: 30000,
  });
}

export function useSkillProgression(candidateId?: string) {
  return useQuery<SkillProgress[], Error>({
    queryKey: ['candidate-skills', candidateId],
    queryFn: () => {
      if (!candidateId) throw new Error('Candidate ID is required');
      return memoryService.getSkillProgression(candidateId);
    },
    enabled: !!candidateId,
    staleTime: 30000,
  });
}

export function useLearningRecommendations(candidateId?: string) {
  return useQuery<LearningRecommendation[], Error>({
    queryKey: ['candidate-recommendations', candidateId],
    queryFn: () => {
      if (!candidateId) throw new Error('Candidate ID is required');
      return memoryService.getLearningRecommendations(candidateId);
    },
    enabled: !!candidateId,
    staleTime: 30000,
  });
}

export function useCompressMemories() {
  const queryClient = useQueryClient();
  return useMutation<MemorySummary, Error, { candidateId: string }>({
    mutationFn: ({ candidateId }) => memoryService.compressMemories(candidateId),
    onSuccess: (_, { candidateId }) => {
      queryClient.invalidateQueries({ queryKey: ['candidate-profile', candidateId] });
      queryClient.invalidateQueries({ queryKey: ['candidate-timeline', candidateId] });
      queryClient.invalidateQueries({ queryKey: ['candidate-recommendations', candidateId] });
    },
  });
}
