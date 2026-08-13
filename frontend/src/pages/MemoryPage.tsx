import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle, Sparkles, Brain } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../stores/AuthStore';
import {
  useCandidateProfile,
  useSkillProgression,
  useCandidateTimeline,
  useLearningRecommendations,
} from '../features/memory/hooks/useMemory';
import { CandidateProfileCard } from '../features/memory/components/CandidateProfileCard';
import { SkillProgressionChart } from '../features/memory/components/SkillProgressionChart';
import { MemoryTimelineList } from '../features/memory/components/MemoryTimelineList';
import { LearningRecommendationsCard } from '../features/memory/components/LearningRecommendationsCard';
import { MemorySummaryCard } from '../features/memory/components/MemorySummaryCard';

export default function MemoryPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const candidateId = user?.id;

  const profileQuery = useCandidateProfile(candidateId);
  const skillsQuery = useSkillProgression(candidateId);
  const timelineQuery = useCandidateTimeline(candidateId);
  const recommendationsQuery = useLearningRecommendations(candidateId);

  const isLoading =
    profileQuery.isLoading ||
    skillsQuery.isLoading ||
    timelineQuery.isLoading ||
    recommendationsQuery.isLoading;

  const isError =
    profileQuery.isError ||
    skillsQuery.isError ||
    timelineQuery.isError ||
    recommendationsQuery.isError;

  const refetchAll = () => {
    profileQuery.refetch();
    skillsQuery.refetch();
    timelineQuery.refetch();
    recommendationsQuery.refetch();
  };

  // 1. LOADING STATE
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center p-8 text-slate-400 space-x-3 font-medium">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
        <span>Fetching candidate memory profile & skill progression...</span>
      </div>
    );
  }

  // 2. ERROR STATE
  if (isError) {
    const errorMsg =
      profileQuery.error?.message ||
      skillsQuery.error?.message ||
      timelineQuery.error?.message ||
      recommendationsQuery.error?.message ||
      'Failed to load candidate memory profile from the server.';

    return (
      <div className="container mx-auto max-w-2xl px-4 py-12 space-y-4">
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-900/60 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
          <h2 className="text-base font-bold text-rose-200">Failed to Load Candidate Memory</h2>
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

  const profileData = profileQuery.data;
  const skillsList = skillsQuery.data || [];
  const timelineList = timelineQuery.data || [];
  const recommendationsList = recommendationsQuery.data || [];

  const hasMemoryData =
    !!profileData ||
    skillsList.length > 0 ||
    timelineList.length > 0 ||
    recommendationsList.length > 0;

  // 3. EMPTY STATE (Candidate has zero memory data recorded)
  if (!hasMemoryData) {
    return (
      <div className="container mx-auto max-w-3xl px-4 py-12">
        <div className="p-8 sm:p-12 rounded-3xl bg-slate-900/90 border border-slate-800 text-center space-y-6 shadow-2xl backdrop-blur-md">
          <div className="h-16 w-16 rounded-2xl bg-indigo-950/80 border border-indigo-800/50 flex items-center justify-center mx-auto text-indigo-400">
            <Brain className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-100 font-display">
              No Memory Profile Recorded Yet
            </h1>
            <p className="text-slate-400 text-xs sm:text-sm max-w-md mx-auto leading-relaxed">
              Complete your first AI interview session to generate personalized long-term memory profiles, skill progression graphs, and learning roadmap recommendations.
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

  // 4. MAIN CANDIDATE MEMORY & PERSONALIZATION VIEW
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 font-display">
          Candidate Long-Term Memory & Personalization
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Longitudinal profile intelligence, skill progression tracking, memory timeline, and personalized learning roadmaps.
        </p>
      </div>

      {/* Candidate Profile Card */}
      <CandidateProfileCard profile={profileData} />

      {/* Skill Progression Recharts Graph */}
      <SkillProgressionChart skills={skillsList} />

      {/* Memory Timeline & Learning Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <MemoryTimelineList timeline={timelineList} />
        <LearningRecommendationsCard recommendations={recommendationsList} />
      </div>

      {/* Memory Synthesis & Compression Action */}
      {candidateId && <MemorySummaryCard candidateId={candidateId} />}
    </div>
  );
}