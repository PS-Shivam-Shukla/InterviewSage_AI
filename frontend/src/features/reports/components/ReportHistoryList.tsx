import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Calendar, FileText, ChevronRight, Sparkles } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { ReportHistoryItem } from '../../../services/report.service';

interface ReportHistoryListProps {
  history: ReportHistoryItem[];
  onSelectReport: (interviewId: string) => void;
}

export const ReportHistoryList: React.FC<ReportHistoryListProps> = ({
  history,
  onSelectReport,
}) => {
  const navigate = useNavigate();

  if (!history || history.length === 0) {
    return (
      <div className="p-8 sm:p-12 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md max-w-xl mx-auto my-12">
        <div className="h-16 w-16 rounded-2xl bg-indigo-950/80 border border-indigo-800/50 flex items-center justify-center mx-auto text-indigo-400">
          <FileText className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-100 font-display">
            No Interview Reports Yet
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm max-w-md mx-auto leading-relaxed">
            Complete your first AI-guided interview session to generate comprehensive competency scorecards and targeted improvement plans.
          </p>
        </div>

        <div className="pt-2 flex justify-center">
          <Button
            onClick={() => navigate('/interviews')}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 px-6 py-2.5 rounded-xl transition-all flex items-center space-x-2 text-sm"
          >
            <Sparkles className="w-4 h-4" />
            <span>Start AI Interview</span>
          </Button>
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 font-display">Interview Reports History</h1>
        <p className="text-xs text-slate-400 mt-1">
          Review your past interview simulations, AI evaluation scorecards, and improvement recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
            <div
              key={item.interview_id}
              className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg backdrop-blur-md flex flex-col justify-between hover:border-slate-700 transition-all space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1 text-xs text-slate-400 font-mono">
                    <Calendar className="w-3.5 h-3.5" />
                    {formattedDate}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${getScoreBadge(scoreVal)}`}>
                    {scoreVal} / 100
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-slate-100 font-display">
                    {item.role || 'Technical Interview'}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {item.total_questions ? `${item.total_questions} Questions Evaluated` : 'Multi-turn Session'}
                  </p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => onSelectReport(item.interview_id)}
                className="w-full justify-between border-slate-800 bg-slate-950/60 text-indigo-300 hover:bg-indigo-950/40 hover:border-indigo-800/60 text-xs font-semibold py-2"
              >
                <div className="flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-indigo-400" />
                  <span>View Detailed Report</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
