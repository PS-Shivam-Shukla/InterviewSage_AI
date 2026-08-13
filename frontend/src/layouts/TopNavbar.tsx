import { useLocation } from "react-router-dom";
import { Menu, Search, User, LogOut } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useAppStore } from "../stores/AppStore";
import { CommandPalette } from "../components/CommandPalette";

interface TopNavbarProps {
  onMobileMenuToggle?: () => void;
}

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": { title: "Command Center", subtitle: "Overview of interview performance and AI metrics" },
  "/resumes": { title: "Resume Intelligence", subtitle: "Manage uploaded resumes and skill parsing" },
  "/interviews": { title: "Live Interview Exam Workspace", subtitle: "Real-time AI voice and technical interview session" },
  "/analytics": { title: "Performance Analytics", subtitle: "Deep-dive diagnostic charts and score trends" },
  "/reports": { title: "Diagnostic Reports", subtitle: "View and download comprehensive report scorecards" },
  "/memory": { title: "Candidate Memory Profile", subtitle: "Longitudinal skill tracking and adaptive context" },
  "/career": { title: "Career Learning Hub", subtitle: "Personalized roadmaps and targeted skill recommendations" },
  "/admin": { title: "Enterprise Operations", subtitle: "System observability, cost telemetry, and review queue" },
  "/settings": { title: "Platform Settings", subtitle: "Configure AI models, profile, and user preferences" },
};

export default function TopNavbar({ onMobileMenuToggle }: TopNavbarProps) {
  const location = useLocation();
  const { user, logout } = useAuth();
  const { setCommandPaletteOpen } = useAppStore();

  const currentPage = pageTitles[location.pathname] || {
    title: "InterviewSage AI",
    subtitle: "Enterprise AI Interview Simulation Platform",
  };

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800/60 bg-slate-950/80 px-4 md:px-6 backdrop-blur-md">
        {/* Left: Mobile Toggle & Page Breadcrumbs */}
        <div className="flex items-center gap-3">
          {onMobileMenuToggle && (
            <button
              onClick={onMobileMenuToggle}
              className="md:hidden rounded-xl p-2 text-slate-400 hover:bg-slate-900 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              aria-label="Open sidebar menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}

          <div>
            <h1 className="text-sm font-bold text-white font-display flex items-center gap-2">
              {currentPage.title}
            </h1>
            <p className="hidden sm:block text-[11px] text-slate-400">
              {currentPage.subtitle}
            </p>
          </div>
        </div>

        {/* Right: Command Palette Trigger & User Profile */}
        <div className="flex items-center gap-3">
          {/* Command Palette Button */}
          <button
            onClick={() => setCommandPaletteOpen(true)}
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-700 hover:bg-slate-900 hover:text-slate-200 transition-all shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            <Search className="h-3.5 w-3.5 text-slate-400" />
            <span className="hidden sm:inline font-medium">Search commands...</span>
          </button>

          {/* User Profile Badge */}
          {user && (
            <div className="flex items-center gap-2 border-l border-slate-800/80 pl-3 ml-1">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 font-bold text-xs">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-semibold text-white leading-tight truncate max-w-[120px]">
                  {user.full_name || "Candidate"}
                </p>
                <p className="text-[10px] text-slate-400 truncate max-w-[120px]">
                  {user.email}
                </p>
              </div>

              <button
                onClick={() => logout()}
                className="ml-1 rounded-lg p-1.5 text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
                title="Log Out"
                aria-label="Log Out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Global Command Palette Modal */}
      <CommandPalette />
    </>
  );
}