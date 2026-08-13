import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Video,
  BarChart3,
  Award,
  BrainCircuit,
  Compass,
  ShieldCheck,
  Settings,
  X,
  Sparkles,
} from "lucide-react";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { title: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { title: "Resumes", path: "/resumes", icon: FileText },
  { title: "Interviews", path: "/interviews", icon: Video },
  { title: "Analytics", path: "/analytics", icon: BarChart3 },
  { title: "Reports", path: "/reports", icon: Award },
  { title: "Memory", path: "/memory", icon: BrainCircuit },
  { title: "Job Descriptions", path: "/career", icon: Compass },
  { title: "Admin", path: "/admin", icon: ShieldCheck },
  { title: "Settings", path: "/settings", icon: Settings },
];

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const content = (
    <aside
      className="flex h-full w-64 flex-col border-r border-slate-800/80 bg-slate-950 text-slate-100 shadow-xl"
      aria-label="Sidebar Navigation"
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800/60">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/20">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <span className="font-display text-lg font-bold tracking-tight text-white">
            InterviewSage <span className="text-indigo-400 text-xs font-mono font-semibold px-1.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 ml-1">AI</span>
          </span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="md:hidden rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            aria-label="Close sidebar navigation"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1.5 px-3 py-4 overflow-y-auto" aria-label="Main Navigation">
        {navItems.map(({ title, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            onClick={onClose}
            className={({ isActive }) =>
              `group flex items-center gap-3.5 rounded-xl px-3.5 py-2.5 text-xs font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-xs"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={`h-4 w-4 shrink-0 transition-colors ${
                    isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"
                  }`}
                />
                <span className="truncate">{title}</span>
                {isActive && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400 shadow-sm shadow-indigo-400/50" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* System Status Footer */}
      <div className="border-t border-slate-800/60 p-4">
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-semibold text-slate-300">LangGraph Agent DAG</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Multi-Agent Engine Connected</p>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <div className="hidden md:flex md:shrink-0">{content}</div>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs transition-opacity"
            onClick={onClose}
            aria-hidden="true"
          />
          <div className="relative flex w-full max-w-xs flex-1">{content}</div>
        </div>
      )}
    </>
  );
}