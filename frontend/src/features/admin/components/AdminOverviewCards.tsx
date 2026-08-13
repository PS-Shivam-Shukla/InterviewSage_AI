import React from 'react';
import { Activity, BarChart3, CheckCircle, Clock, DollarSign } from 'lucide-react';
import { AdminDashboardSummary } from '../types/admin.types';

interface AdminOverviewCardsProps {
  summary?: AdminDashboardSummary;
}

export const AdminOverviewCards: React.FC<AdminOverviewCardsProps> = ({ summary }) => {
  const active = summary?.active_interviews ?? 0;
  const total = summary?.total_interviews ?? 0;
  const passRate = summary?.success_rate != null ? `${summary.success_rate.toFixed(1)}%` : 'N/A';
  const avgLatency = summary?.avg_latency_ms != null ? `${Math.round(summary.avg_latency_ms)} ms` : 'N/A';
  const totalCost = summary?.total_token_cost_usd != null ? `$${summary.total_token_cost_usd.toFixed(4)}` : '$0.0000';

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Live Active Sessions</span>
          <Activity className="h-4 w-4 text-emerald-400 animate-pulse" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {active}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total Interviews</span>
          <BarChart3 className="h-4 w-4 text-indigo-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {total}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Pass Rate</span>
          <CheckCircle className="h-4 w-4 text-blue-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {passRate}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Avg Latency</span>
          <Clock className="h-4 w-4 text-amber-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {avgLatency}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md sm:col-span-2 lg:col-span-1">
        <div className="flex items-center justify-between text-slate-400">
          <span className="text-xs font-semibold uppercase tracking-wider">Total AI Token Cost</span>
          <DollarSign className="h-4 w-4 text-emerald-400" />
        </div>
        <p className="mt-3 text-3xl font-extrabold text-slate-100 font-mono tracking-tight">
          {totalCost}
        </p>
      </div>
    </div>
  );
};
