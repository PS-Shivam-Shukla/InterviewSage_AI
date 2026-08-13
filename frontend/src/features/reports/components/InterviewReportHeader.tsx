import React, { useState } from 'react';
import { ArrowLeft, Download, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { useDownloadReportPdf } from '../hooks/useReports';

interface InterviewReportHeaderProps {
  interviewId: string;
  role: string;
  generatedAt: string;
  status: string;
  onBack: () => void;
}

export const InterviewReportHeader: React.FC<InterviewReportHeaderProps> = ({
  interviewId,
  role,
  generatedAt,
  status,
  onBack,
}) => {
  const downloadPdfMutation = useDownloadReportPdf();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    setDownloadError(null);
    try {
      const blob = await downloadPdfMutation.mutateAsync({ interviewId });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `interview_report_${interviewId.substring(0, 8)}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setDownloadError(err?.message || 'Failed to download PDF report.');
    }
  };

  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Recent';

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
            className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Reports
          </Button>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-100 font-display">
                {role || 'Technical Interview'} Performance Report
              </h1>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <CheckCircle2 className="w-3 h-3" />
                {status || 'COMPLETED'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Generated on {formattedDate} · Comprehensive Multi-Agent Evaluation
            </p>
          </div>
        </div>

        <Button
          onClick={handleDownloadPdf}
          disabled={downloadPdfMutation.isPending}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-xl transition-all shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 text-sm"
        >
          {downloadPdfMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating PDF...</span>
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              <span>Download PDF Report</span>
            </>
          )}
        </Button>
      </div>

      {downloadError && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}
    </div>
  );
};
