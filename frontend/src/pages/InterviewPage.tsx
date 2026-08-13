import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Play, AlertCircle, Loader2, Sparkles, CheckCircle2, Award, FileText, Briefcase } from 'lucide-react';
import { apiClient } from '../api/client';
import { useInterviewStore } from '../features/interview/store/InterviewStore';
import { useInterviewPlan } from '../features/interview/hooks/useInterviewPlan';
import { useSubmitAnswer } from '../features/interview/hooks/useSubmitAnswer';
import { useCreateInterview } from '../features/interview/hooks/useCreateInterview';
import { useResumeList } from '../features/resume/hooks/useResumeList';
import { useListJobDescriptions } from '../hooks/useJobDescription';
import { AIAvatar } from '../features/interview/components/AIAvatar';
import { InterviewHeader } from '../features/interview/components/InterviewHeader';
import { InterviewProgress } from '../features/interview/components/InterviewProgress';
import { InterviewQuestionCard } from '../features/interview/components/InterviewQuestionCard';
import { InterviewAnswerInput } from '../features/interview/components/InterviewAnswerInput';
import { InterviewEvaluationCard } from '../features/interview/components/InterviewEvaluationCard';
import { InterviewMetricsPanel } from '../features/interview/components/InterviewMetricsPanel';
import { Button } from '../components/ui/Button';

export default function InterviewPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const {
    activeInterview,
    isPaused,
    aiState,
    metrics,
    setAIState,
    setIsPaused,
    setActiveInterview,
    updateMetrics,
  } = useInterviewStore();

  const { data: resumes } = useResumeList();
  const { data: savedJds } = useListJobDescriptions();
  const { data: planData, isLoading: isPlanLoading, isError: isPlanError } = useInterviewPlan(activeInterview?.id);
  const submitAnswerMutation = useSubmitAnswer();
  const createInterviewMutation = useCreateInterview();

  const [selectedResumeId, setSelectedResumeId] = useState<string>(searchParams.get('resumeId') || '');
  const [selectedJdId, setSelectedJdId] = useState<string>(searchParams.get('jdId') || '');

  const [activeQuestion, setActiveQuestion] = useState<any>(null);
  const [nextQuestionPending, setNextQuestionPending] = useState<any>(null);
  const [lastEvaluation, setLastEvaluation] = useState<any>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Live Timer Effect
  useEffect(() => {
    if (!activeInterview || isPaused || activeInterview.status === 'COMPLETED') return;
    const timer = setInterval(() => {
      updateMetrics({ timeElapsedSeconds: (metrics.timeElapsedSeconds || 0) + 1 });
    }, 1000);
    return () => clearInterval(timer);
  }, [activeInterview, isPaused, metrics.timeElapsedSeconds, updateMetrics]);

  // Sync default selection from loaded resumes & JDs if searchParams not provided
  useEffect(() => {
    if (resumes && resumes.length > 0 && !selectedResumeId) {
      setSelectedResumeId(resumes[0].id);
    }
  }, [resumes, selectedResumeId]);

  useEffect(() => {
    if (savedJds && savedJds.length > 0 && !selectedJdId) {
      setSelectedJdId(savedJds[0].id);
    }
  }, [savedJds, selectedJdId]);

  // Sync initial question from backend plan response
  useEffect(() => {
    if (planData) {
      const plan = (planData as any).plan || planData;
      const firstQ = plan.first_question || plan.blueprint?.questions?.[0] || activeInterview?.current_question;
      if (firstQ && !activeQuestion) {
        setActiveQuestion({
          id: firstQ.id || '',
          sequence_number: firstQ.sequence_number || 1,
          round_type: firstQ.type || firstQ.round_type || 'TECHNICAL',
          competency: firstQ.competency || firstQ.competency_focus || '',
          difficulty: firstQ.difficulty || 'MEDIUM',
          // No hardcoded fallback — if question_text is missing, show loading state
          text: firstQ.text || firstQ.question_text || '',
        });
      }
    }
  }, [planData, activeInterview, activeQuestion]);

  // Handle Answer Submission Flow
  const handleAnswerSubmit = async (answerText: string) => {
    if (!activeInterview || !activeQuestion) return;

    setSubmitError(null);
    setAIState('THINKING');

    try {
      const response = await submitAnswerMutation.mutateAsync({
        interview_id: activeInterview.id,
        question_id: activeQuestion.id || 'q-1',
        question_text: activeQuestion.text,
        answer: answerText,
      });

      if (response?.evaluation) {
        setLastEvaluation(response.evaluation);
        const evalScore = Number(response.evaluation.score) || 0;
        updateMetrics({
          technicalScore: Math.round(evalScore),
          communicationScore: Number(response.evaluation.communication_score) || Math.round(evalScore),
          confidenceScore: Number(response.evaluation.confidence_score) || Math.round(evalScore),
          currentCompetency: activeQuestion.competency || response.evaluation.competency_targeted || '',
          currentDifficulty: activeQuestion.difficulty || 'MEDIUM',
        });
      }

      if (response?.status === 'COMPLETED') {
        setActiveInterview({ ...activeInterview, status: 'COMPLETED' });
      } else if (response?.next_question) {
        setNextQuestionPending(response.next_question);
      }

      setAIState('IDLE');
    } catch (err: any) {
      setAIState('IDLE');
      setSubmitError(err?.response?.data?.detail || err?.message || 'Failed to evaluate answer. Please try again.');
    }
  };

  // Handle Proceeding to Next Question
  const handleNextQuestion = () => {
    if (nextQuestionPending) {
      setActiveQuestion({
        id: nextQuestionPending.id,
        sequence_number: nextQuestionPending.sequence_number,
        round_type: nextQuestionPending.round_type || 'TECHNICAL',
        competency: nextQuestionPending.competency || 'System Architecture',
        difficulty: nextQuestionPending.difficulty || 'MEDIUM',
        text: nextQuestionPending.text,
      });
      setNextQuestionPending(null);
    }
    setLastEvaluation(null);
  };

  // Handle Voice Turn STT Result from WebSocket
  const handleVoiceTurnComplete = useCallback(
    (data: any) => {
      if (data?.evaluation) {
        setLastEvaluation(data.evaluation);
        const evalScore = Number(data.evaluation.score) || 0;
        updateMetrics({
          technicalScore: Math.round(evalScore),
          communicationScore: Number(data.evaluation.communication_score) || Math.round(evalScore),
          confidenceScore: Number(data.evaluation.confidence_score) || Math.round(evalScore),
          currentCompetency: activeQuestion?.competency || data.evaluation.competency_targeted || '',
          currentDifficulty: activeQuestion?.difficulty || 'MEDIUM',
        });
      }

      if (data?.status === 'COMPLETED' || data?.interview_status === 'COMPLETED') {
        if (activeInterview) {
          setActiveInterview({ ...activeInterview, status: 'COMPLETED' });
        }
      } else if (data?.next_question) {
        const nq = data.next_question;
        setNextQuestionPending({
          id: nq.id || '',
          sequence_number: nq.sequence_number || (activeQuestion?.sequence_number || 1) + 1,
          round_type: nq.round_type || nq.type || 'TECHNICAL',
          competency: nq.competency_targeted || nq.competency || 'General',
          difficulty: nq.difficulty || 'MEDIUM',
          text: nq.question_text || nq.text || '',
        });
      }
    },
    [activeInterview, activeQuestion, updateMetrics, setActiveInterview]
  );

  // Handle Cancel / End Session
  const handleCancelInterview = async () => {
    if (!activeInterview) return;
    const confirmCancel = window.confirm('Are you sure you want to cancel and exit this interview session?');
    if (!confirmCancel) return;

    try {
      await apiClient.post(`/interviews/${activeInterview.id}/complete`);
    } catch {
      // Ignore completion errors on exit
    } finally {
      setActiveInterview(null);
      setLastEvaluation(null);
      setNextQuestionPending(null);
      setActiveQuestion(null);
    }
  };

  const [isLaunchingSession, setIsLaunchingSession] = useState<boolean>(false);

  const handleCreateSession = async () => {
    if (isLaunchingSession || createInterviewMutation.isPending) return;
    setIsLaunchingSession(true);

    try {
      const targetJd = savedJds?.find((j) => j.id === selectedJdId);
      const resolvedRole = targetJd?.target_role || '';
      await createInterviewMutation.mutateAsync({
        resume_id: selectedResumeId || undefined,
        jd_id: selectedJdId || undefined,
        target_role: resolvedRole,
        target_company: targetJd?.company_name || 'InterviewSage AI',
        interview_mode: 'TEXT',
        difficulty: 'ADAPTIVE',
      });
      // Reset metrics to zero at interview start — no fake initial values
      updateMetrics({
        technicalScore: 0,
        communicationScore: 0,
        confidenceScore: 0,
        currentCompetency: '',
        currentDifficulty: 'MEDIUM',
        timeElapsedSeconds: 0,
      });
    } catch (err) {
      console.error("Failed to launch interview session:", err);
    } finally {
      setIsLaunchingSession(false);
    }
  };

  // 1. NO ACTIVE INTERVIEW STATE
  if (!activeInterview) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-12">
        <div className="p-8 lg:p-12 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
          <div className="h-16 w-16 rounded-2xl bg-indigo-950/80 border border-indigo-800/50 flex items-center justify-center mx-auto text-indigo-400">
            <Sparkles className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 font-display">
              Launch Tailored Multi-Agent Interview
            </h1>
            <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
              Launch a live interview session using your target Resume & Job Description to generate personalized questions in real time.
            </p>
          </div>

          {/* Selector Dropdowns for Resume & Job Description */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg mx-auto text-left pt-2">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-emerald-400" /> Resume Target
              </label>
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-indigo-500 focus:outline-none"
              >
                <option value="">Default Demo Resume</option>
                {resumes?.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.file_path ? r.file_path.split(/[/\\\\]/).pop() : `Resume (${r.id.slice(0, 8)})`}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5 text-blue-400" /> Job Description Target
              </label>
              <select
                value={selectedJdId}
                onChange={(e) => setSelectedJdId(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-indigo-500 focus:outline-none"
              >
                <option value="">Default Demo Job Description</option>
                {savedJds?.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.target_role} {j.company_name ? `(${j.company_name})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="pt-4 flex justify-center">
            <Button
              onClick={handleCreateSession}
              disabled={createInterviewMutation.isPending || isLaunchingSession}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 px-8 py-3 rounded-xl transition-all flex items-center space-x-2 text-base disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createInterviewMutation.isPending || isLaunchingSession ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Initializing Multi-Agent Session...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  <span>Start Live Multi-Agent Session</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 2. LOADING STATE
  if (isPlanLoading) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-16 text-center space-y-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mx-auto" />
        <p className="text-slate-300 font-medium">Assembling multi-agent question pipeline from backend...</p>
      </div>
    );
  }

  // 3. ERROR STATE
  if (isPlanError) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-12">
        <div className="p-8 rounded-2xl bg-rose-950/40 border border-rose-900/60 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-rose-200">Failed to Load Interview Session</h2>
          <p className="text-sm text-slate-300">An error occurred while fetching the interview plan from the server.</p>
          <Button onClick={() => window.location.reload()} variant="outline" className="border-rose-800 text-rose-300">
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  // 4. COMPLETED SESSION STATE
  if (activeInterview.status === 'COMPLETED') {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-12">
        <div className="p-8 lg:p-12 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
          <div className="h-16 w-16 rounded-2xl bg-emerald-950/80 border border-emerald-800/50 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl lg:text-3xl font-bold text-slate-100 font-display">
              Interview Complete
            </h1>
            <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
              Your performance report is ready! All question turns have been evaluated via the EvaluationAgent and persisted to PostgreSQL.
            </p>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row justify-center gap-4">
            <Button
              onClick={() => {
                const targetId = (activeInterview as any).report_id || activeInterview.id;
                setActiveInterview(null);
                navigate(`/reports/${targetId}`);
              }}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <Award className="w-5 h-5 text-indigo-200" />
              <span>View Performance Report</span>
            </Button>
            <Button
              onClick={() => setActiveInterview(null)}
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800 px-6 py-3 rounded-xl transition-all"
            >
              Start Another Interview
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // 5. LIVE INTERVIEW SESSION VIEW
  return (
    <div className="container mx-auto max-w-7xl px-4 py-6 space-y-6">
      {/* Top Session Header */}
      <InterviewHeader
        interview={activeInterview}
        isPaused={isPaused}
        onTogglePause={() => setIsPaused(!isPaused)}
        onEndSession={handleCancelInterview}
      />

      {/* Progress Bar */}
      <InterviewProgress
        currentQuestionIndex={activeQuestion?.sequence_number || 1}
        totalQuestions={activeInterview.total_questions || (planData as any)?.blueprint_items?.length || 5}
        currentCompetency={activeQuestion?.competency}
      />

      {/* Main Grid Layout: Desktop (2 Columns: Main 8-col, Sidebar 4-col) | Mobile (Stacked) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left/Main Content Column (8 cols on desktop) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Animated AI Avatar Container */}
          <div className="p-8 rounded-2xl bg-slate-900/70 border border-slate-800/80 flex items-center justify-center backdrop-blur-md shadow-xl">
            <AIAvatar state={aiState} />
          </div>

          {/* Active Question Card */}
          <InterviewQuestionCard
            question={activeQuestion}
            sequenceNumber={activeQuestion?.sequence_number || 1}
          />

          {/* Answer Input (Visible when last turn is not evaluated or when proceeding) */}
          <InterviewAnswerInput
            interviewId={activeInterview?.id}
            onSubmit={handleAnswerSubmit}
            onVoiceTurnComplete={handleVoiceTurnComplete}
            isSubmitting={aiState === 'THINKING' || submitAnswerMutation.isPending}
            isDisabled={isPaused || !!lastEvaluation}
            error={submitError}
          />

          {/* Backend Evaluation Results Card (Appears after answer is evaluated) */}
          <InterviewEvaluationCard
            evaluation={lastEvaluation}
            onNextQuestion={handleNextQuestion}
            hasNextQuestion={!!nextQuestionPending}
          />
        </div>

        {/* Right Sidebar Column (4 cols on desktop) */}
        <div className="lg:col-span-4 space-y-6">
          <InterviewMetricsPanel metrics={metrics} />
        </div>
      </div>
    </div>
  );
}