import { useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';
import { Resume } from '../types/resume.types';

export function useUploadResume(onUploadProgress?: (progress: number) => void) {
  const queryClient = useQueryClient();

  return useMutation<Resume, Error, File>({
    mutationFn: (file: File) => resumeService.uploadResume(file, onUploadProgress),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resume-analysis', data?.id] });
      queryClient.invalidateQueries({ queryKey: ['resume-analysis'] });
    },
  });
}
