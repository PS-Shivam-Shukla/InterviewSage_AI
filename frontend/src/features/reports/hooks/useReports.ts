import { useQuery, useMutation } from '@tanstack/react-query';
import { reportService, InterviewReportResponse, ReportHistoryItem } from '../../../services/report.service';

export function useReportHistory() {
  return useQuery<ReportHistoryItem[], Error>({
    queryKey: ['reports-history'],
    queryFn: reportService.getReportHistory,
    staleTime: 30000,
  });
}

export function useInterviewReport(interviewId?: string) {
  return useQuery<InterviewReportResponse, Error>({
    queryKey: ['interview-report', interviewId],
    queryFn: () => {
      if (!interviewId) throw new Error('Interview ID is required');
      return reportService.getInterviewReport(interviewId);
    },
    enabled: !!interviewId,
    staleTime: 60000,
  });
}

export function useDownloadReportPdf() {
  return useMutation<Blob, Error, { interviewId: string }>({
    mutationFn: ({ interviewId }) => reportService.downloadInterviewReportPdf(interviewId),
  });
}
