import { motion } from 'framer-motion';
import { Sparkles, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface AuthLayoutShellProps {
  children: React.ReactNode;
}

export function AuthLayoutShell({ children }: AuthLayoutShellProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(37,99,235,0.14),_transparent_55%)] px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-5xl overflow-hidden rounded-[28px] border border-neutral-200 bg-white shadow-[0_20px_60px_rgba(15,23,42,0.08)] dark:border-neutral-800 dark:bg-neutral-900"
      >
        <div className="grid lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left Gradient Hero Panel */}
          <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-700 p-8 text-white lg:p-10 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-blue-100 font-mono">
                <Sparkles className="h-4 w-4" />
                InterviewSage Agentic Engine
              </div>

              <h1 className="mt-6 text-4xl font-semibold tracking-tight font-display leading-tight">
                Prepare for top tech interviews with confidence.
              </h1>

              <p className="mt-4 max-w-md text-sm leading-7 text-blue-50/90">
                InterviewSage combines multi-agent resume parsing, role-specific question synthesis, and live AI feedback in one calm enterprise workspace.
              </p>

              <div className="mt-8 space-y-3 rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="h-5 w-5 text-blue-200 shrink-0" />
                  <span className="text-sm">JWT-backed authentication & token security</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-blue-200 shrink-0" />
                  <span className="text-sm">Tailored FAANG-grade question banks & feedback</span>
                </div>
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-blue-200 shrink-0" />
                  <span className="text-sm">Comprehensive performance reports & ATS score</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-white/15 text-xs text-blue-100/80">
              © 2026 InterviewSage AI Inc. All rights reserved.
            </div>
          </div>

          {/* Right Form Panel */}
          <div className="p-8 lg:p-10 flex flex-col justify-center">
            {children}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
