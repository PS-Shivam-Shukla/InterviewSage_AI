import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';
import { Resume } from '../types/resume.types';

interface ReplaceParams {
  resumeId: string;
  file: File;
}

export function useReplaceResume() {
  const queryClient = useQueryClient();

  return useMutation<Resume, Error, ReplaceParams>({
    mutationFn: ({ resumeId, file }) => resumeService.replaceResume(resumeId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resume', variables.resumeId] });
      queryClient.invalidateQueries({ queryKey: ['resume-analysis', variables.resumeId] });
    },
  });
}
