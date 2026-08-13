import { useState, FormEvent } from "react";
import { useAuth } from "../hooks/useAuth";
import { useUpdateProfile, useExportData } from "../features/settings/hooks/useSettings";
import { User, Shield, Download, Moon, Sun, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "../components/ui/Button";

export default function SettingsPage() {
  const { user } = useAuth();
  const updateProfileMutation = useUpdateProfile();
  const exportDataMutation = useExportData();

  const [fullName, setFullName] = useState<string>(user?.full_name || "");
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);

  const handleSubmitProfile = async (e: FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    setErrorMsg(null);

    if (!user?.id) return;

    try {
      await updateProfileMutation.mutateAsync({ userId: user.id, fullName });
      setSuccessMsg("Profile updated successfully.");
    } catch (err: any) {
      setErrorMsg(err?.message || "Failed to update profile.");
    }
  };

  const handleExport = async () => {
    if (!user?.id) return;
    try {
      await exportDataMutation.mutateAsync(user.id);
    } catch (err: any) {
      alert("Failed to export data: " + (err?.message || "Server error"));
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white font-display">Account & Preferences</h1>
        <p className="text-xs text-neutral-400">
          Manage your personal profile, security configuration, data export, and environment theme settings.
        </p>
      </div>

      {/* User Profile Form Card */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
        <div className="flex items-center gap-2 border-b border-neutral-800 pb-4 text-white font-bold text-sm">
          <User className="h-4 w-4 text-blue-400" />
          Profile Configuration
        </div>

        {successMsg && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs font-medium text-emerald-400">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs font-medium text-rose-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmitProfile} className="space-y-4 max-w-lg">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-neutral-300">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              placeholder="Your Full Name"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-neutral-300">Email Address (Read Only)</label>
            <input
              type="email"
              value={user?.email || ""}
              disabled
              className="w-full rounded-xl border border-neutral-800 bg-neutral-950/60 px-3.5 py-2.5 text-xs text-neutral-500 cursor-not-allowed"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-neutral-300">User ID</label>
            <input
              type="text"
              value={user?.id || ""}
              disabled
              className="w-full rounded-xl border border-neutral-800 bg-neutral-950/60 px-3.5 py-2.5 text-xs text-neutral-500 font-mono cursor-not-allowed"
            />
          </div>

          <Button
            type="submit"
            disabled={updateProfileMutation.isPending}
            className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-2.5 px-5 shadow-sm"
          >
            {updateProfileMutation.isPending ? "Saving..." : "Save Profile Changes"}
          </Button>
        </form>
      </div>

      {/* Security & Data Export Card */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
        <div className="flex items-center gap-2 border-b border-neutral-800 pb-4 text-white font-bold text-sm">
          <Shield className="h-4 w-4 text-purple-400" />
          Data Sovereignty & Privacy
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white">Export Full Profile & Analytics Data</h3>
            <p className="text-[11px] text-neutral-400 mt-0.5">
              Download your full interview transcript history, evaluation scores, and parsed resume data in JSON format.
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleExport}
            disabled={exportDataMutation.isPending}
            className="rounded-xl border-neutral-700 text-xs font-semibold hover:bg-neutral-800 text-white"
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            {exportDataMutation.isPending ? "Exporting..." : "Export Data"}
          </Button>
        </div>
      </div>

      {/* Theme Preference Card */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
        <div className="flex items-center gap-2 border-b border-neutral-800 pb-4 text-white font-bold text-sm">
          {isDarkMode ? <Moon className="h-4 w-4 text-amber-400" /> : <Sun className="h-4 w-4 text-amber-400" />}
          Interface Preferences
        </div>

        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white">Theme Mode</h3>
            <p className="text-[11px] text-neutral-400 mt-0.5">
              Active theme: <span className="font-mono text-neutral-200">{isDarkMode ? "Dark Mode" : "Light Mode"}</span>
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={() => setIsDarkMode((prev) => !prev)}
            className="rounded-xl border-neutral-700 text-xs font-semibold hover:bg-neutral-800 text-white"
          >
            Switch to {isDarkMode ? "Light Mode" : "Dark Mode"}
          </Button>
        </div>
      </div>
    </div>
  );
}
