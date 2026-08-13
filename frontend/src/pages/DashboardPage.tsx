import { useNavigate } from "react-router-dom";
import { useDashboard } from "../features/dashboard/hooks/useDashboard";
import { useAuth } from "../hooks/useAuth";
import { Award, BarChart3, Clock, AlertTriangle, TrendingUp, CheckCircle, Play, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "../components/ui/Button";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { summary, trends, competencies } = useDashboard();

  if (summary.isLoading || trends.isLoading || competencies.isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400">
        <div className="flex items-center gap-3 font-medium text-xs">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          Loading command center analytics...
        </div>
      </div>
    );
  }

  if (summary.isError || trends.isError || competencies.isError) {
    return (
      <div className="p-6 md:p-8">
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 text-sm text-rose-400 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>Failed to load dashboard metrics from backend.</span>
          </div>
          <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const summaryData = summary.data;
  const trendList = trends.data || [];
  const compList = competencies.data || [];

  return (
    <div className="space-y-6 p-4 md:p-6 max-w-7xl mx-auto">
      {/* Premium Hero Welcome Section */}
      <div className="relative overflow-hidden rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-300">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Multi-Agent LangGraph Engine Active</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-white font-display tracking-tight">
              Welcome back, {user?.full_name ? user.full_name.split(" ")[0] : "Candidate"} 👋
            </h1>
            <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Track your preparation telemetry, review real-time feedback, and conduct your next AI-orchestrated technical interview simulation.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Button
              onClick={() => navigate("/resumes")}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-5 py-3 rounded-xl shadow-lg shadow-indigo-600/30 flex items-center gap-2 group transition-all"
            >
              <Play className="h-4 w-4 fill-white" />
              <span>Start New Interview</span>
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 shadow-xs hover:border-slate-700/80 transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Interviews</span>
            <div className="rounded-xl bg-blue-500/10 p-2 text-blue-400">
              <BarChart3 className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-3xl font-bold text-white font-mono">
            {summaryData?.total_interviews ?? 0}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">Completed sessions</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 shadow-xs hover:border-slate-700/80 transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Average Score</span>
            <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-400">
              <Award className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-3xl font-bold text-white font-mono">
            {summaryData?.average_score != null ? `${summaryData.average_score.toFixed(1)}%` : "N/A"}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">Overall evaluation score</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 shadow-xs hover:border-slate-700/80 transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Completion Rate</span>
            <div className="rounded-xl bg-purple-500/10 p-2 text-purple-400">
              <CheckCircle className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-3xl font-bold text-white font-mono">
            {summaryData?.completion_rate != null
              ? `${(summaryData.completion_rate * 100).toFixed(0)}%`
              : "0%"}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">Question round completion</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-5 shadow-xs hover:border-slate-700/80 transition-all">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">In Progress</span>
            <div className="rounded-xl bg-amber-500/10 p-2 text-amber-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-3xl font-bold text-white font-mono">
            {summaryData?.in_progress_count ?? 0}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">Active sessions</p>
        </div>
      </div>

      {/* Weak Competencies Alert Card */}
      {summaryData?.weak_competencies && summaryData.weak_competencies.length > 0 && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5">
          <div className="flex items-center gap-2 text-amber-400">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <h2 className="text-xs font-bold uppercase tracking-wider">Recommended Areas for Focus</h2>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {summaryData.weak_competencies.map((area) => (
              <span
                key={area}
                className="rounded-xl border border-amber-500/30 bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-300"
              >
                {area}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Score Trend & Competencies Panels */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Score Trend Card */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-indigo-400" />
              <h2 className="text-sm font-bold text-white">Score Trends Over Time</h2>
            </div>
            <button
              onClick={() => navigate("/reports")}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
            >
              View Reports →
            </button>
          </div>
          {trendList.length === 0 ? (
            <div className="py-8 text-center space-y-2">
              <p className="text-xs text-slate-400">No interview score history recorded yet.</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate("/resumes")}
                className="text-xs border-slate-700 text-slate-300"
              >
                Start First Interview
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {trendList.map((item, idx) => (
                <div key={item.interview_id || idx} className="flex items-center justify-between text-xs border-b border-slate-800/60 pb-2.5">
                  <span className="text-slate-400 font-mono text-[11px]">{item.date}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-28 md:w-36 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${Math.min(item.score, 100)}%` }}
                      />
                    </div>
                    <span className="font-bold text-white font-mono w-10 text-right">{item.score}%</span>
                    {item.interview_id && (
                      <button
                        onClick={() => navigate(`/reports/${item.interview_id}`)}
                        className="text-[11px] text-indigo-400 hover:underline font-semibold ml-1"
                      >
                        Report
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Competencies Progress Card */}
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-4 w-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-white">Competency Breakdown</h2>
          </div>
          {compList.length === 0 ? (
            <p className="text-xs text-slate-400 py-8 text-center">
              No competency evaluation metrics available yet.
            </p>
          ) : (
            <div className="space-y-4">
              {compList.map((comp) => (
                <div key={comp.competency} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{comp.competency}</span>
                    <span className="font-mono text-emerald-400 font-bold">{comp.avg_score.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-2 rounded-full"
                      style={{ width: `${Math.min(comp.avg_score, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}