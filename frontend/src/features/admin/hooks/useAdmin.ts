import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../../services/admin.service';
import {
  AdminDashboardSummary,
  LiveInterviewItem,
  InterviewTimeline,
  PromptHistoryItem,
  ReviewQueueItem,
  ReviewStatus,
  CostAnalytics,
} from '../types/admin.types';

export function useAdminDashboard() {
  return useQuery<AdminDashboardSummary, Error>({
    queryKey: ['admin-dashboard'],
    queryFn: adminService.getDashboardSummary,
    staleTime: 15000,
  });
}

export function useLiveInterviews() {
  return useQuery<LiveInterviewItem[], Error>({
    queryKey: ['admin-live-interviews'],
    queryFn: adminService.getLiveInterviews,
    staleTime: 10000,
  });
}

export function useInterviewTimeline(interviewId?: string) {
  return useQuery<InterviewTimeline, Error>({
    queryKey: ['admin-timeline', interviewId],
    queryFn: () => {
      if (!interviewId) throw new Error('Interview ID is required');
      return adminService.getInterviewTimeline(interviewId);
    },
    enabled: !!interviewId,
    staleTime: 30000,
  });
}

export function usePromptHistory() {
  return useQuery<PromptHistoryItem[], Error>({
    queryKey: ['admin-prompt-history'],
    queryFn: adminService.getPromptHistory,
    staleTime: 60000,
  });
}

export function useCostAnalytics() {
  return useQuery<CostAnalytics, Error>({
    queryKey: ['admin-cost-analytics'],
    queryFn: adminService.getCostAnalytics,
    staleTime: 30000,
  });
}

export function useReviewQueue(statusFilter?: string) {
  return useQuery<ReviewQueueItem[], Error>({
    queryKey: ['admin-review-queue', statusFilter],
    queryFn: () => adminService.getReviewQueue(statusFilter),
    staleTime: 15000,
  });
}

export function useProcessReviewStatus() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string; status: string }, Error, { reviewId: string; statusVal: ReviewStatus }>({
    mutationFn: ({ reviewId, statusVal }) => adminService.processReviewStatus(reviewId, statusVal),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
    },
  });
}
