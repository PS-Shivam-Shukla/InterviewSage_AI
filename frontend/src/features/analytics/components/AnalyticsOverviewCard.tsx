import React from 'react';
import { BarChart3, Award, CheckCircle, Clock, Star } from 'lucide-react';
import { AnalyticsSummary, TrendItem } from '../types/analytics.types';

interface AnalyticsOverviewCardProps {
  summary?: AnalyticsSummary;
  trends?: TrendItem[];
}

export const AnalyticsOverviewCard: React.FC<AnalyticsOverviewCardProps> = ({ summary, trends }) => {
  const total = summary?.total_interviews ?? 0;
  const avgScore = summary?.average_score != null ? `${summary.average_score.toFixed(1)}%` : 'N/A';
  const completionRate = summary?.completion_rate != null ? `${(summary.completion_rate * 100).toFixed(0)}%` : '0%';
  const inProgress = summary?.in_progress_count ?? 0;

  // Derive best score from trends if available
  const bestScore = trends && trends.length > 0
    ? `${Math.max(...trends.map((t) => t.score))}%`
    : avgScore;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total Interviews</span>
          <BarChart3 className="h-4 w-4 text-blue-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {total}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Average Score</span>
          <Award className="h-4 w-4 text-emerald-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {avgScore}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Completion Rate</span>
          <CheckCircle className="h-4 w-4 text-indigo-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {completionRate}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">In Progress</span>
          <Clock className="h-4 w-4 text-amber-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {inProgress}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md sm:col-span-2 lg:col-span-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Best Score</span>
          <Star className="h-4 w-4 text-yellow-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {bestScore}
        </p>
      </div>
    </div>
  );
};
