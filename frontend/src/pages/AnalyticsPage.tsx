import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, Sparkles, BarChart3 } from 'lucide-react';
import { Button } from '../components/ui/Button';
import {
  useAnalyticsSummary,
  useAnalyticsTrends,
  useAnalyticsCompetencies,
  useAnalyticsVoice,
} from '../features/analytics/hooks/useAnalytics';
import { useReportHistory } from '../features/reports/hooks/useReports';
import { AnalyticsOverviewCard } from '../features/analytics/components/AnalyticsOverviewCard';
import { PerformanceTrendChart } from '../features/analytics/components/PerformanceTrendChart';
import { CompetencyRadarChart } from '../features/analytics/components/CompetencyRadarChart';
import { VoiceAnalyticsCard } from '../features/analytics/components/VoiceAnalyticsCard';
import { ImprovementInsightsCard } from '../features/analytics/components/ImprovementInsightsCard';
import { AnalyticsHistoryTable } from '../features/analytics/components/AnalyticsHistoryTable';

export default function AnalyticsPage() {
  const navigate = useNavigate();

  const summaryQuery = useAnalyticsSummary();
  const trendsQuery = useAnalyticsTrends();
  const competenciesQuery = useAnalyticsCompetencies();
  const voiceQuery = useAnalyticsVoice();
  const historyQuery = useReportHistory();

  const isLoading =
    summaryQuery.isLoading ||
    trendsQuery.isLoading ||
    competenciesQuery.isLoading ||
    voiceQuery.isLoading;

  const isError =
    summaryQuery.isError ||
    trendsQuery.isError ||
    competenciesQuery.isError ||
    voiceQuery.isError;

  const refetchAll = () => {
    summaryQuery.refetch();
    trendsQuery.refetch();
    competenciesQuery.refetch();
    voiceQuery.refetch();
    historyQuery.refetch();
  };

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400 space-x-3 font-medium">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        <span>Aggregating real-time performance analytics...</span>
      </div>
    );
  }

  // 2. ERROR STATE
  if (isError) {
    const errorMsg =
      summaryQuery.error?.message ||
      trendsQuery.error?.message ||
      competenciesQuery.error?.message ||
      voiceQuery.error?.message ||
      'Failed to fetch analytics metrics from the server.';

    return (
      <div className="container mx-auto max-w-2xl px-4 py-12 space-y-4">
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-900/60 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-rose-200">Failed to Load Performance Analytics</h2>
          <p className="text-xs text-slate-300">{errorMsg}</p>
          <div className="flex justify-center gap-3 pt-2">
            <Button onClick={refetchAll} variant="outline" className="border-rose-800 text-rose-300 text-xs">
              Retry Loading
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const summaryData = summaryQuery.data;
  const trendList = trendsQuery.data || [];
  const compList = competenciesQuery.data || [];
  const voiceData = voiceQuery.data;
  const historyList = historyQuery.data || [];

  const totalInterviews = summaryData?.total_interviews ?? 0;

  // 3. EMPTY STATE (Candidate has zero total interviews)
  if (totalInterviews === 0) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-12">
        <div className="p-8 sm:p-12 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
          <div className="h-16 w-16 rounded-2xl bg-indigo-950/80 border border-indigo-800/50 flex items-center justify-center mx-auto text-indigo-400">
            <BarChart3 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-100 font-display">
              No Analytics Available Yet
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm max-w-md mx-auto leading-relaxed">
              Complete your first AI interview session to start tracking performance score trends, competency breakdowns, and acoustic voice metrics.
            </p>
          </div>

          <div className="pt-2 flex justify-center">
            <Button
              onClick={() => navigate('/interviews')}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 px-8 py-3 rounded-xl transition-all flex items-center space-x-2 text-sm"
            >
              <Sparkles className="w-4 h-4" />
              <span>Start AI Interview</span>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 4. MAIN ANALYTICS DASHBOARD VIEW
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 font-display">
          Candidate Longitudinal Analytics
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Truthful performance analytics aggregated directly from your persisted interview evaluations & acoustic voice metrics.
        </p>
      </div>

      {/* Metrics Overview Bar */}
      <AnalyticsOverviewCard summary={summaryData} trends={trendList} />

      {/* Charts Grid: Performance Trends & Competencies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <PerformanceTrendChart trends={trendList} />
        <CompetencyRadarChart competencies={compList} />
      </div>

      {/* Voice Performance Card & Improvement Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7">
          <VoiceAnalyticsCard voice={voiceData} />
        </div>
        <div className="lg:col-span-5">
          <ImprovementInsightsCard weakCompetencies={summaryData?.weak_competencies} />
        </div>
      </div>

      {/* Evaluated Interview History Table */}
      <AnalyticsHistoryTable history={historyList} />
    </div>
  );
}