import React from 'react';
import { UserCheck, Award, AlertCircle, Briefcase, Sparkles } from 'lucide-react';
import { CandidateProfile } from '../types/memory.types';

interface CandidateProfileCardProps {
  profile?: CandidateProfile;
}

export const CandidateProfileCard: React.FC<CandidateProfileCardProps> = ({ profile }) => {
  if (!profile) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
        <h2 className="text-sm font-bold text-slate-100">Candidate Memory Profile</h2>
        <p className="text-xs text-slate-400 mt-1">No profile information available yet.</p>
      </div>
    );
  }

  const skillsList = profile.skills || [];
  const strengthsList = profile.strengths || [];
  const weaknessesList = profile.weaknesses || [];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-indigo-950/80 border border-indigo-800/50 flex items-center justify-center text-indigo-400 shrink-0">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 font-display">
                Candidate Personalization Profile
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                Level: {profile.current_level || 'MID'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-slate-500" />
              <span>{profile.experience_years || 0} Years Experience</span>
            </p>
          </div>
        </div>
      </div>

      {profile.summary && (
        <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Longitudinal Memory Summary</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-mono">
            {profile.summary}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Verified Skills */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Verified Skills
          </span>
          {skillsList.length === 0 ? (
            <p className="text-xs text-slate-500">No skills verified yet.</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {skillsList.map((skill) => (
                <span
                  key={skill}
                  className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-800 border border-slate-700 text-slate-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Identified Strengths */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
            <Award className="w-3.5 h-3.5" />
            Core Strengths
          </span>
          {strengthsList.length === 0 ? (
            <p className="text-xs text-slate-500">No strengths recorded yet.</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {strengthsList.map((str) => (
                <span
                  key={str}
                  className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                >
                  {str}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Identified Weaknesses */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
          <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" />
            Focus Areas
          </span>
          {weaknessesList.length === 0 ? (
            <p className="text-xs text-slate-500">No focus areas recorded.</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {weaknessesList.map((weak) => (
                <span
                  key={weak}
                  className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-300"
                >
                  {weak}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
