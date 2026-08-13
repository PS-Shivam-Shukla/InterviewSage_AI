import { useInterviewStore } from '../store/InterviewStore';

export function useInterviewMetrics() {
  const { metrics, updateMetrics } = useInterviewStore();

  return {
    metrics,
    updateMetrics,
  };
}
