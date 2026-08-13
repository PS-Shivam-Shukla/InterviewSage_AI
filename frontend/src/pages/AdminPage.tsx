import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, ShieldAlert, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/Button';
import {
  useAdminDashboard,
  useLiveInterviews,
  useReviewQueue,
  useCostAnalytics,
  usePromptHistory,
} from '../features/admin/hooks/useAdmin';
import { AdminOverviewCards } from '../features/admin/components/AdminOverviewCards';
import { LiveInterviewsMonitor } from '../features/admin/components/LiveInterviewsMonitor';
import { HumanReviewQueueCard } from '../features/admin/components/HumanReviewQueueCard';
import { AICostBreakdownCard } from '../features/admin/components/AICostBreakdownCard';
import { PromptHistoryExplorer } from '../features/admin/components/PromptHistoryExplorer';

export default function AdminPage() {
  const navigate = useNavigate();

  const dashboardQuery = useAdminDashboard();
  const liveQuery = useLiveInterviews();
  const queueQuery = useReviewQueue();
  const costsQuery = useCostAnalytics();
  const promptsQuery = usePromptHistory();

  const isLoading =
    dashboardQuery.isLoading ||
    liveQuery.isLoading ||
    queueQuery.isLoading ||
    costsQuery.isLoading ||
    promptsQuery.isLoading;

  const isForbidden =
    (dashboardQuery.error as any)?.response?.status === 403 ||
    (liveQuery.error as any)?.response?.status === 403 ||
    (queueQuery.error as any)?.response?.status === 403 ||
    (costsQuery.error as any)?.response?.status === 403 ||
    (promptsQuery.error as any)?.response?.status === 403;

  const isError =
    !isForbidden &&
    (dashboardQuery.isError ||
      liveQuery.isError ||
      queueQuery.isError ||
      costsQuery.isError ||
      promptsQuery.isError);

  const refetchAll = () => {
    dashboardQuery.refetch();
    liveQuery.refetch();
    queueQuery.refetch();
    costsQuery.refetch();
    promptsQuery.refetch();
  };

  // 1. NON-ADMIN ACCESS RESTRICTION (403 FORBIDDEN)
  if (isForbidden) {
    return (
      <div className="container mx-auto max-w-2xl px-4 py-12 space-y-4">
        <div className="p-8 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-4 shadow-2xl backdrop-blur-md">
          <div className="h-16 w-16 rounded-2xl bg-amber-950/80 border border-amber-800/50 flex items-center justify-center mx-auto text-amber-400">
            <ShieldAlert className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-slate-100 font-display">Admin Access Required</h2>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              This area is restricted to authorized platform administrators and recruiters. Your account does not have permission to view AI Platform Operations.
            </p>
          </div>

          <div className="pt-2 flex justify-center">
            <Button
              onClick={() => navigate('/dashboard')}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-6 py-2.5 rounded-xl transition-all flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Dashboard</span>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 2. LOADING STATE
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400 space-x-3 font-medium">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        <span>Loading AI Platform Operations & Live Metrics...</span>
      </div>
    );
  }

  // 3. GENERAL ERROR STATE
  if (isError) {
    const errorMsg =
      dashboardQuery.error?.message ||
      liveQuery.error?.message ||
      queueQuery.error?.message ||
      costsQuery.error?.message ||
      promptsQuery.error?.message ||
      'Failed to fetch enterprise admin operations metrics.';

    return (
      <div className="container mx-auto max-w-2xl px-4 py-12 space-y-4">
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-900/60 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-rose-200">Failed to Load Enterprise Operations</h2>
          <p className="text-xs text-slate-300">{errorMsg}</p>
          <div className="flex justify-center gap-3 pt-2">
            <Button onClick={refetchAll} variant="outline" className="border-rose-800 text-rose-300 text-xs gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Operations
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const dashboardData = dashboardQuery.data;
  const liveSessions = liveQuery.data || [];
  const reviewQueue = queueQuery.data || [];
  const costAnalytics = costsQuery.data;
  const promptHistory = promptsQuery.data || [];

  // 4. MAIN ENTERPRISE OPERATIONS DASHBOARD VIEW
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 font-display">
            Enterprise AI Platform Operations
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time session monitoring, human review queue processing, cost breakdowns, and prompt template auditing.
          </p>
        </div>

        <Button
          onClick={refetchAll}
          variant="outline"
          className="border-slate-800 text-slate-300 hover:bg-slate-900 text-xs gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Operations</span>
        </Button>
      </div>

      {/* Overview Cards Bar */}
      <AdminOverviewCards summary={dashboardData} />

      {/* Live Interview Session Monitor */}
      <LiveInterviewsMonitor liveSessions={liveSessions} />

      {/* Human Review Queue & AI Cost Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <HumanReviewQueueCard queue={reviewQueue} />
        <AICostBreakdownCard costs={costAnalytics} />
      </div>

      {/* Prompt Version History Explorer */}
      <PromptHistoryExplorer promptHistory={promptHistory} />
    </div>
  );
}