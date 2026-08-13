import React from 'react';
import { TrendingUp, FileText } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { TrendItem } from '../types/analytics.types';
import { AccessibleDataTable } from '../../../components/ui/AccessibleDataTable';

interface PerformanceTrendChartProps {
  trends?: TrendItem[];
}

export const PerformanceTrendChart: React.FC<PerformanceTrendChartProps> = ({ trends }) => {
  if (!trends || trends.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">Performance Score Trends</h2>
        </div>
        <div className="py-12 text-center space-y-2">
          <FileText className="w-8 h-8 text-slate-600 mx-auto" aria-hidden="true" />
          <p className="text-xs text-slate-400">
            No interview score trends recorded yet. Complete sessions to track your progression over time.
          </p>
        </div>
      </div>
    );
  }

  const chartData = trends.map((item) => ({
    date: item.date,
    score: Math.round(item.score),
  }));

  const tableHeaders = ['Date', 'Score (%)'];
  const tableRows = chartData.map((d) => [d.date, `${d.score}%`]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <AccessibleDataTable
        caption="Historical Performance Progression Over Time"
        headers={tableHeaders}
        rows={tableRows}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">Performance Progression Over Time</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{trends.length} Sessions Recorded</span>
      </div>

      <div className="h-64 w-full pt-2" aria-label="Performance trend chart graph">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(value: number) => [`${value}%`, 'Score']}
            />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#6366f1"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#scoreGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
