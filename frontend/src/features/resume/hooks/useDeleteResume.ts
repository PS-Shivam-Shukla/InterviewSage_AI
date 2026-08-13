import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';

export function useDeleteResume() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (resumeId: string) => resumeService.deleteResume(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
    },
  });
}
