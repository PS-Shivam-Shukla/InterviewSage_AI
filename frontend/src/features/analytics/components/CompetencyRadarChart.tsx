import React from 'react';
import { BarChart2, ShieldCheck } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import { CompetencyItem } from '../types/analytics.types';
import { AccessibleDataTable } from '../../../components/ui/AccessibleDataTable';

interface CompetencyRadarChartProps {
  competencies?: CompetencyItem[];
}

export const CompetencyRadarChart: React.FC<CompetencyRadarChartProps> = ({ competencies }) => {
  if (!competencies || competencies.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <BarChart2 className="h-5 w-5 text-emerald-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">Competency Breakdown</h2>
        </div>
        <div className="py-12 text-center space-y-2">
          <ShieldCheck className="w-8 h-8 text-slate-600 mx-auto" aria-hidden="true" />
          <p className="text-xs text-slate-400">
            No competency evaluations recorded yet. Complete interview turns to build your competency profile.
          </p>
        </div>
      </div>
    );
  }

  const chartData = competencies.map((item) => ({
    name: item.competency,
    score: Math.round(item.avg_score),
    count: item.interview_count,
  }));

  const tableHeaders = ['Competency', 'Average Score (%)', 'Interview Count'];
  const tableRows = chartData.map((d) => [d.name, `${d.score}%`, d.count]);

  const getBarColor = (score: number) => {
    if (score >= 85) return '#10b981'; // emerald
    if (score >= 75) return '#6366f1'; // indigo
    if (score >= 60) return '#f59e0b'; // amber
    return '#f43f5e'; // rose
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <AccessibleDataTable
        caption="Competency Mastery Breakdown Data"
        headers={tableHeaders}
        rows={tableRows}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart2 className="h-5 w-5 text-emerald-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">Competency Mastery Breakdown</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{competencies.length} Skill Categories</span>
      </div>

      <div className="h-72 w-full pt-2" aria-label="Competency mastery bar chart graph">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="name"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              interval={0}
              angle={-45}
              textAnchor="end"
              height={75}
              tickFormatter={(val: string) => (val && val.length > 18 ? `${val.substring(0, 16)}...` : val)}
            />
            <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(value: number, _name: string, item: any) => [
                `${value}%`,
                item?.payload?.name || 'Avg Score',
              ]}
            />
            <Bar dataKey="score" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
