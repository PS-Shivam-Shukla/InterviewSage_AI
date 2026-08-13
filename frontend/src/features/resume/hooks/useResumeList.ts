import { useQuery } from '@tanstack/react-query';
import { resumeService } from '../services/resume.service';
import { Resume } from '../types/resume.types';

export function useResumeList() {
  return useQuery<Resume[], Error>({
    queryKey: ['resumes'],
    queryFn: () => resumeService.listResumes(),
  });
}
