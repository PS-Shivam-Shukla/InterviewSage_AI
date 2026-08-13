import React from 'react';
import { Mic, Zap, Clock, Activity, Volume2, Shield } from 'lucide-react';
import { VoiceAnalyticsSummary } from '../types/analytics.types';

interface VoiceAnalyticsCardProps {
  voice?: VoiceAnalyticsSummary;
}

export const VoiceAnalyticsCard: React.FC<VoiceAnalyticsCardProps> = ({ voice }) => {
  if (!voice || !voice.has_voice_data) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <Mic className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Voice Acoustic Analytics</h2>
        </div>

        <div className="p-8 rounded-xl border border-slate-800/80 bg-slate-950/60 text-center space-y-3">
          <Volume2 className="w-8 h-8 text-slate-600 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-slate-200">No Voice Interview Sessions Recorded Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              Complete a live voice interview simulation to measure acoustic speaking speed (WPM), answer latency, silence duration, and AI confidence estimates.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Mic className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Acoustic & Voice Performance Summary</h2>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
          {voice.voice_sessions_count} Voice Sessions
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Speaking Speed</span>
          </div>
          <p className="text-2xl font-bold text-slate-100 font-mono">
            {voice.avg_speaking_speed_wpm} <span className="text-xs font-normal text-slate-400">WPM</span>
          </p>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>Answer Latency</span>
          </div>
          <p className="text-2xl font-bold text-slate-100 font-mono">
            {voice.avg_answer_latency_seconds} <span className="text-xs font-normal text-slate-400">sec</span>
          </p>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span>Total Speaking Time</span>
          </div>
          <p className="text-2xl font-bold text-slate-100 font-mono">
            {voice.total_speaking_time_seconds} <span className="text-xs font-normal text-slate-400">sec</span>
          </p>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Confidence Estimate</span>
          </div>
          <p className="text-2xl font-bold text-slate-100 font-mono">
            {voice.avg_confidence_estimate}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-800/60">
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800/80">
          <span className="text-xs text-slate-400">Words Spoken Total</span>
          <span className="text-sm font-bold text-slate-100 font-mono">{voice.total_words_spoken}</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800/80">
          <span className="text-xs text-slate-400">Communication Score</span>
          <span className="text-sm font-bold text-indigo-400 font-mono">{voice.avg_communication_score}%</span>
        </div>

        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800/80">
          <span className="text-xs text-slate-400">Technical Depth Score</span>
          <span className="text-sm font-bold text-emerald-400 font-mono">{voice.avg_technical_score}%</span>
        </div>
      </div>
    </div>
  );
};
