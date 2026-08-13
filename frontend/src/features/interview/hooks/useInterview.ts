import { useQuery } from '@tanstack/react-query';
import { interviewService } from '../services/interview.service';
import { Interview } from '../types/interview.types';

export function useInterview(interviewId?: string) {
  return useQuery<Interview, Error>({
    queryKey: ['interview', interviewId],
    queryFn: () => interviewService.getInterview(interviewId!),
    enabled: !!interviewId,
  });
}
