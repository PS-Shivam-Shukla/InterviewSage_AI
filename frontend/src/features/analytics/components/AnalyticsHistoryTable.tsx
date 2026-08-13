import React from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Calendar, ExternalLink, FileText } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { ReportHistoryItem } from '../../../services/report.service';

interface AnalyticsHistoryTableProps {
  history?: ReportHistoryItem[];
}

export const AnalyticsHistoryTable: React.FC<AnalyticsHistoryTableProps> = ({ history }) => {
  const navigate = useNavigate();

  if (!history || history.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Interview History & Reports</h2>
        </div>
        <div className="py-8 text-center space-y-2">
          <FileText className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-xs text-slate-400">
            No completed interview reports available. Complete your first session to see historical results.
          </p>
        </div>
      </div>
    );
  }

  const getScoreBadge = (score: number) => {
    const rounded = Math.round(score);
    if (rounded >= 85) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    if (rounded >= 75) return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
    if (rounded >= 60) return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Evaluated Interview History</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{history.length} Reports Persisted</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Date</th>
              <th className="py-3 px-4">Role / Title</th>
              <th className="py-3 px-4">Score</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {history.map((item) => {
              const formattedDate = item.generated_at || item.completed_at
                ? new Date(item.generated_at || item.completed_at!).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })
                : 'Recent';

              const scoreVal = Math.round(item.overall_score ?? 0);

              return (
                <tr key={item.interview_id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      <span>{formattedDate}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-semibold text-slate-100 whitespace-nowrap">
                    {item.role || 'Technical Interview'}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className={`px-2.5 py-0.5 rounded-full font-mono font-bold border ${getScoreBadge(scoreVal)}`}>
                      {scoreVal}%
                    </span>
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold text-[11px]">
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/reports/${item.interview_id}`)}
                      className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/30 text-xs gap-1"
                    >
                      <span>View Report</span>
                      <ExternalLink className="w-3 h-3" />
                    </Button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
