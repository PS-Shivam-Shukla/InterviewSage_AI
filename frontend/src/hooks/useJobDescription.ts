import { useMutation, useQuery } from '@tanstack/react-query';
import {
  jdService,
  JobDescriptionCreatePayload,
  JobDescriptionResponse,
  JobDescriptionMatchResponse,
} from '../services/jd.service';

export function useCreateJobDescription() {
  return useMutation<JobDescriptionResponse, Error, JobDescriptionCreatePayload>({
    mutationFn: (payload: JobDescriptionCreatePayload) => jdService.createJobDescription(payload),
  });
}

export function useJobDescription(id?: string) {
  return useQuery<JobDescriptionResponse, Error>({
    queryKey: ['job-description', id],
    queryFn: () => jdService.getJobDescription(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.required_skills && data.required_skills.length > 0) {
        return false;
      }
      return 2000;
    },
  });
}

export function useListJobDescriptions() {
  return useQuery<JobDescriptionResponse[], Error>({
    queryKey: ['job-descriptions'],
    queryFn: () => jdService.listJobDescriptions(),
  });
}

export function useMatchResumeWithJd() {
  return useMutation<JobDescriptionMatchResponse, Error, { jdId: string; resumeId: string }>({
    mutationFn: ({ jdId, resumeId }) => jdService.matchResumeWithJd(jdId, resumeId),
  });
}
