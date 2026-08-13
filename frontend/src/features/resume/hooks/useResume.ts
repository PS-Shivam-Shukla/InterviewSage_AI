import { useQuery } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';
import { Resume } from '../types/resume.types';

export function useResume(resumeId?: string) {
  return useQuery<Resume, Error>({
    queryKey: ['resume', resumeId],
    queryFn: () => resumeService.getResume(resumeId!),
    enabled: !!resumeId,
  });
}
