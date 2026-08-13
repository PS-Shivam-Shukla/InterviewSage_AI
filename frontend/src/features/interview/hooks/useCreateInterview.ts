import { useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewService } from '../services/interview.service';
import { CreateInterviewPayload, Interview } from '../types/interview.types';
import { useInterviewStore } from '../store/InterviewStore';

export function useCreateInterview() {
  const queryClient = useQueryClient();
  const setActiveInterview = useInterviewStore((state) => state.setActiveInterview);

  return useMutation<Interview, Error, CreateInterviewPayload>({
    mutationFn: (payload) => interviewService.createInterview(payload),
    onSuccess: (data) => {
      setActiveInterview(data);
      queryClient.invalidateQueries({ queryKey: ['interviews'] });
    },
  });
}
