import { useQuery } from '@tanstack/react-query';
import { interviewService } from '../services/interview.service';
import { InterviewPlan } from '../types/interview.types';

export function useInterviewPlan(interviewId?: string) {
  return useQuery<InterviewPlan, Error>({
    queryKey: ['interview-plan', interviewId],
    queryFn: () => interviewService.getInterviewPlan(interviewId!),
    enabled: !!interviewId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if plan is not yet loaded or doesn't have questions yet
      const plan = query.state.data ? ((query.state.data as any).plan || query.state.data) : null;
      if (!plan || !plan.first_question) {
        return 2000;
      }
      return false;
    },
  });
}
