import { apiClient } from '../api/client';
import {
  AdminDashboardSummary,
  LiveInterviewItem,
  InterviewTimeline,
  PromptHistoryItem,
  ReviewQueueItem,
  ReviewStatus,
  CostAnalytics,
} from '../features/admin/types/admin.types';

export const adminService = {
  async getDashboardSummary(): Promise<AdminDashboardSummary> {
    const res = await apiClient.get<AdminDashboardSummary>('/admin/dashboard');
    return res.data;
  },

  async getLiveInterviews(): Promise<LiveInterviewItem[]> {
    const res = await apiClient.get<LiveInterviewItem[]>('/admin/interviews/live');
    return res.data;
  },

  async getInterviewTimeline(interviewId: string): Promise<InterviewTimeline> {
    const res = await apiClient.get<InterviewTimeline>(`/admin/interview/${interviewId}/timeline`);
    return res.data;
  },

  async getPromptHistory(): Promise<PromptHistoryItem[]> {
    const res = await apiClient.get<PromptHistoryItem[]>('/admin/prompts/history');
    return res.data;
  },

  async getCostAnalytics(): Promise<CostAnalytics> {
    const res = await apiClient.get<CostAnalytics>('/admin/analytics/costs');
    return res.data;
  },

  async getReviewQueue(statusFilter?: string): Promise<ReviewQueueItem[]> {
    const params = statusFilter ? { status: statusFilter } : {};
    const res = await apiClient.get<ReviewQueueItem[]>('/admin/review/queue', { params });
    return res.data;
  },

  async processReviewStatus(
    reviewId: string,
    statusVal: ReviewStatus
  ): Promise<{ message: string; status: string }> {
    const res = await apiClient.post<{ message: string; status: string }>(
      `/admin/review/${reviewId}/status`,
      null,
      { params: { status: statusVal } }
    );
    return res.data;
  },
};
