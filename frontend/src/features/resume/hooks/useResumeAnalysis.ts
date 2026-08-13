import { useQuery } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';
import { Resume, ResumeAnalysis } from '../types/resume.types';

export function useResumeAnalysis(resumeId?: string) {
  return useQuery<ResumeAnalysis, Error>({
    queryKey: ['resume-analysis', resumeId],
    queryFn: () => resumeService.getResumeAnalysis(resumeId!),
    enabled: !!resumeId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      // Authoritative polling: poll strictly while PROCESSING; stop on COMPLETED or FAILED
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        return false;
      }
      return 2000;
    },
  });
}

export function useResume(resumeId?: string) {
  return useQuery<Resume, Error>({
    queryKey: ['resume', resumeId],
    queryFn: () => resumeService.getResume(resumeId!),
    enabled: !!resumeId,
  });
}
