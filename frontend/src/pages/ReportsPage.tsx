import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useReportHistory, useInterviewReport } from '../features/reports/hooks/useReports';
import { InterviewReportHeader } from '../features/reports/components/InterviewReportHeader';
import { OverallScoreCard } from '../features/reports/components/OverallScoreCard';
import { CompetencyScorecard } from '../features/reports/components/CompetencyScorecard';
import { ImprovementPlanCard } from '../features/reports/components/ImprovementPlanCard';
import { TranscriptSnapshotAccordion } from '../features/reports/components/TranscriptSnapshotAccordion';
import { ReportHistoryList } from '../features/reports/components/ReportHistoryList';

export default function ReportsPage() {
  const { interviewId } = useParams<{ interviewId?: string }>();
  const navigate = useNavigate();

  // Mode 1: Detailed Report View for /reports/:interviewId
  if (interviewId) {
    return <ReportDetailView interviewId={interviewId} onBack={() => navigate('/reports')} />;
  }

  // Mode 2: Report History View for /reports
  return <ReportHistoryView onSelectReport={(id) => navigate(`/reports/${id}`)} />;
}

function ReportHistoryView({ onSelectReport }: { onSelectReport: (id: string) => void }) {
  const { data: history, isLoading, isError, error, refetch } = useReportHistory();

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400 space-x-3 font-medium">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        <span>Loading interview reports history...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6 max-w-2xl mx-auto space-y-4">
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-5 text-rose-400 space-y-2">
          <div className="flex items-center gap-2 font-bold text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Failed to Load Reports History</span>
          </div>
          <p className="text-xs text-rose-300">
            {error?.message || 'An error occurred while communicating with the server.'}
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" size="sm" className="border-rose-800 text-rose-300">
          Retry Loading
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <ReportHistoryList history={history || []} onSelectReport={onSelectReport} />
    </div>
  );
}

function ReportDetailView({ interviewId, onBack }: { interviewId: string; onBack: () => void }) {
  const navigate = useNavigate();
  const { data: report, isLoading, isError, error, refetch } = useInterviewReport(interviewId);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400 space-x-3 font-medium">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        <span>Fetching multi-agent evaluation report...</span>
      </div>
    );
  }

  if (isError) {
    const errMessage = error?.message || '';
    const is404 = errMessage.includes('404') || errMessage.includes('not found');
    const isInProgress = errMessage.includes('IN_PROGRESS') || errMessage.includes('400');

    if (is404) {
      return (
        <div className="container mx-auto max-w-xl px-4 py-12">
          <div className="p-8 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
            <div className="h-14 w-14 rounded-2xl bg-rose-950/80 border border-rose-800/50 flex items-center justify-center mx-auto text-rose-400">
              <AlertCircle className="w-7 h-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-100 font-display">Report Not Found</h2>
              <p className="text-slate-400 text-xs leading-relaxed max-w-md mx-auto">
                This interview report could not be found or may have been deleted.
              </p>
            </div>
            <Button onClick={onBack} className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-6 py-2 rounded-xl">
              Back to Reports History
            </Button>
          </div>
        </div>
      );
    }

    if (isInProgress) {
      return (
        <div className="container mx-auto max-w-xl px-4 py-12">
          <div className="p-8 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
            <div className="h-14 w-14 rounded-2xl bg-amber-950/80 border border-amber-800/50 flex items-center justify-center mx-auto text-amber-400">
              <AlertCircle className="w-7 h-7" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-100 font-display">Interview In Progress</h2>
              <p className="text-slate-400 text-xs leading-relaxed max-w-md mx-auto">
                Your final performance report will become available once the interview session is marked as completed.
              </p>
            </div>
            <div className="flex justify-center gap-3">
              <Button onClick={() => navigate('/interviews')} className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-6 py-2 rounded-xl">
                Go to Active Interview
              </Button>
              <Button onClick={onBack} variant="outline" className="border-slate-800 text-slate-300 text-xs px-4 py-2 rounded-xl">
                Back to Reports
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="container mx-auto max-w-2xl px-4 py-12 space-y-4">
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-900/60 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-rose-200">Failed to Load Report</h2>
          <p className="text-xs text-slate-300">{errMessage || 'An unexpected error occurred.'}</p>
          <div className="flex justify-center gap-3 pt-2">
            <Button onClick={() => refetch()} variant="outline" className="border-rose-800 text-rose-300 text-xs">
              Retry Connection
            </Button>
            <Button onClick={onBack} variant="outline" className="border-slate-800 text-slate-300 text-xs">
              Back to Reports
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8 space-y-6">
      <InterviewReportHeader
        interviewId={report.interview_id}
        role={report.role}
        generatedAt={report.generated_at}
        status={report.status}
        onBack={onBack}
      />

      <OverallScoreCard score={report.overall_score} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <CompetencyScorecard scorecard={report.competency_scorecard} />
        <ImprovementPlanCard plan={report.improvement_plan} />
      </div>

      <TranscriptSnapshotAccordion transcript={report.transcript_snapshot} />
    </div>
  );
}