import { useState, useEffect, FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useCreateJobDescription, useListJobDescriptions, useMatchResumeWithJd } from "../hooks/useJobDescription";
import { useResumeList } from "../features/resume/hooks/useResumeList";
import { JobDescriptionResponse, JobDescriptionMatchResponse } from "../services/jd.service";
import { Briefcase, Building, Sparkles, CheckCircle2, AlertCircle, Layers, ArrowRight, Play, FileText, Target, Award } from "lucide-react";
import { Button } from "../components/ui/Button";

export default function CareerPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Queries & Mutations
  const { data: resumes } = useResumeList();
  const { data: savedJds } = useListJobDescriptions();
  const createJdMutation = useCreateJobDescription();
  const matchMutation = useMatchResumeWithJd();

  // State
  const [selectedResumeId, setSelectedResumeId] = useState<string>(searchParams.get("resumeId") || "");
  const [selectedJdId, setSelectedJdId] = useState<string>("");
  const [targetRole, setTargetRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [rawText, setRawText] = useState("");
  const [analyzedJd, setAnalyzedJd] = useState<JobDescriptionResponse | null>(null);
  const [matchResult, setMatchResult] = useState<JobDescriptionMatchResponse | null>(null);
  const [processingStage, setProcessingStage] = useState<string>("");

  // Sync default selected resume ID when resumes load
  useEffect(() => {
    if (resumes && resumes.length > 0 && !selectedResumeId) {
      setSelectedResumeId(resumes[0].id);
    }
  }, [resumes, selectedResumeId]);

  // Handle Match Calculation when both Resume and JD are selected
  const handleCalculateMatch = async (jdId: string, resumeId: string) => {
    if (!jdId || !resumeId) return;
    try {
      const match = await matchMutation.mutateAsync({ jdId, resumeId });
      setMatchResult(match);
    } catch (err) {
      console.error("Failed to compute ATS match score:", err);
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!rawText.trim() || !targetRole.trim()) return;

    try {
      setProcessingStage("Analyzing Job Description & extracting skill competencies with AI agents...");

      const result = await createJdMutation.mutateAsync({
        raw_text: rawText,
        target_role: targetRole,
        company_name: companyName || undefined,
        industry: industry || undefined,
      });

      setAnalyzedJd(result);
      setSelectedJdId(result.id);
      setProcessingStage("");

      // Trigger automatic ATS matching if a resume is selected
      if (selectedResumeId) {
        await handleCalculateMatch(result.id, selectedResumeId);
      }
    } catch (err) {
      console.error("Job Description analysis failed:", err);
      setProcessingStage("");
    }
  };

  // Handle selecting an existing saved JD
  const handleSelectSavedJd = (jd: JobDescriptionResponse) => {
    setAnalyzedJd(jd);
    setSelectedJdId(jd.id);
    setTargetRole(jd.target_role);
    setCompanyName(jd.company_name || "");
    setIndustry(jd.industry || "");
    if (selectedResumeId) {
      handleCalculateMatch(jd.id, selectedResumeId);
    }
  };

  // Handle selecting a resume for matching
  const handleResumeChange = (resumeId: string) => {
    setSelectedResumeId(resumeId);
    if (selectedJdId && resumeId) {
      handleCalculateMatch(selectedJdId, resumeId);
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-white font-display">Job Description & ATS Intelligence</h1>
        <p className="text-xs text-neutral-400">
          Analyze job postings, extract required technical competencies, and measure candidate compatibility before launching a live interview.
        </p>
      </div>

      {/* Step Progress Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className={`p-3 rounded-xl border flex items-center gap-3 ${selectedResumeId ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" : "border-neutral-800 bg-neutral-900/40 text-neutral-400"}`}>
          <div className="h-7 w-7 rounded-lg bg-emerald-500/20 flex items-center justify-center font-bold text-xs font-mono">1</div>
          <div className="min-w-0">
            <p className="text-xs font-semibold">Select Resume</p>
            <p className="text-[10px] text-neutral-400 truncate">{resumes?.find(r => r.id === selectedResumeId)?.file_path?.split(/[/\\\\]/).pop() || "None selected"}</p>
          </div>
        </div>

        <div className={`p-3 rounded-xl border flex items-center gap-3 ${analyzedJd ? "border-blue-500/40 bg-blue-500/10 text-blue-300" : "border-neutral-800 bg-neutral-900/40 text-neutral-400"}`}>
          <div className="h-7 w-7 rounded-lg bg-blue-500/20 flex items-center justify-center font-bold text-xs font-mono">2</div>
          <div className="min-w-0">
            <p className="text-xs font-semibold">Job Description</p>
            <p className="text-[10px] text-neutral-400 truncate">{analyzedJd ? analyzedJd.target_role : "Paste / Upload JD"}</p>
          </div>
        </div>

        <div className={`p-3 rounded-xl border flex items-center gap-3 ${matchResult ? "border-purple-500/40 bg-purple-500/10 text-purple-300" : "border-neutral-800 bg-neutral-900/40 text-neutral-400"}`}>
          <div className="h-7 w-7 rounded-lg bg-purple-500/20 flex items-center justify-center font-bold text-xs font-mono">3</div>
          <div className="min-w-0">
            <p className="text-xs font-semibold">ATS Compatibility</p>
            <p className="text-[10px] text-neutral-400 truncate">{matchResult ? `${matchResult.ats_score}% Skill Match` : "Pending Analysis"}</p>
          </div>
        </div>

        <div className={`p-3 rounded-xl border flex items-center gap-3 ${matchResult ? "border-indigo-500/40 bg-indigo-500/10 text-indigo-300" : "border-neutral-800 bg-neutral-900/40 text-neutral-400 opacity-60"}`}>
          <div className="h-7 w-7 rounded-lg bg-indigo-500/20 flex items-center justify-center font-bold text-xs font-mono">4</div>
          <div className="min-w-0">
            <p className="text-xs font-semibold">Interview Setup</p>
            <p className="text-[10px] text-neutral-400 truncate">Tailored Multi-Agent</p>
          </div>
        </div>
      </div>

      {/* Target Resume Selection Bar */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-neutral-300">
          <FileText className="h-4 w-4 text-emerald-400" />
          <span>Target Candidate Resume:</span>
        </div>
        <select
          value={selectedResumeId}
          onChange={(e) => handleResumeChange(e.target.value)}
          className="w-full sm:w-auto min-w-[280px] rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none"
        >
          <option value="" disabled>Select an uploaded resume...</option>
          {resumes?.map((r) => (
            <option key={r.id} value={r.id}>
              {r.file_path ? r.file_path.split(/[/\\\\]/).pop() : `Resume (${r.id.slice(0, 8)})`}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left Column: Job Description Submission Form */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-4 text-white font-bold text-sm">
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-blue-400" />
              Analyze New Job Description
            </div>
            {savedJds && savedJds.length > 0 && (
              <span className="text-[10px] font-mono text-neutral-400">
                {savedJds.length} Saved JD(s)
              </span>
            )}
          </div>

          {/* Quick Select Saved JDs */}
          {savedJds && savedJds.length > 0 && (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-neutral-400">Quick Select Saved Job Posting:</label>
              <div className="flex flex-wrap gap-2">
                {savedJds.slice(0, 3).map((jd) => (
                  <button
                    key={jd.id}
                    onClick={() => handleSelectSavedJd(jd)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                      selectedJdId === jd.id
                        ? "border-blue-500 bg-blue-500/20 text-blue-300"
                        : "border-neutral-800 bg-neutral-950 text-neutral-400 hover:text-white hover:border-neutral-700"
                    }`}
                  >
                    {jd.target_role} {jd.company_name ? `(${jd.company_name})` : ""}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-300">Target Role Title *</label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g. Senior Full Stack Engineer"
                className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-neutral-300">Company Name</label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Corp"
                  className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-neutral-300">Industry Sector</label>
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="e.g. FinTech / AI"
                  className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-300">Job Description Raw Text *</label>
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                rows={7}
                placeholder="Paste the full job posting requirements, responsibilities, and qualifications here..."
                className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-3.5 py-2.5 text-xs text-white shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none font-mono text-[11px]"
                required
              />
            </div>

            {createJdMutation.isPending && processingStage && (
              <div className="flex items-center gap-2 rounded-xl border border-blue-500/20 bg-blue-500/10 p-3 text-xs text-blue-400">
                <Sparkles className="h-4 w-4 shrink-0 animate-spin" />
                <span>{processingStage}</span>
              </div>
            )}

            {createJdMutation.isError && (
              <div className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>Failed to analyze job description. Check network connection.</span>
              </div>
            )}

            <Button
              type="submit"
              disabled={createJdMutation.isPending}
              className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-3 shadow-md shadow-blue-600/20"
            >
              {createJdMutation.isPending ? (
                <>
                  <Sparkles className="mr-1.5 h-4 w-4 animate-spin" /> Analyzing Job Requirements...
                </>
              ) : (
                "Extract Skill Competencies & Run JDAgent"
              )}
            </Button>
          </form>
        </div>

        {/* Right Column: Parsed AI Job Analysis & ATS Match Summary */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 space-y-6 min-h-[400px]">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-4 text-white font-bold text-sm">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              AI Parsed Job Intelligence & ATS Match
            </div>
          </div>

          {!analyzedJd ? (
            <div className="flex flex-col items-center justify-center py-20 text-center text-neutral-500">
              <Briefcase className="h-10 w-10 text-neutral-700 mb-3" />
              <p className="text-xs font-medium">
                Submit a job description on the left to extract skill requirements, seniority level, and calculate ATS compatibility score.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Header Info */}
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-white">{analyzedJd.target_role}</h3>
                    <p className="text-xs text-neutral-400 flex items-center gap-2 mt-1">
                      {analyzedJd.company_name && (
                        <span className="flex items-center gap-1">
                          <Building className="h-3 w-3 text-neutral-500" />
                          {analyzedJd.company_name}
                        </span>
                      )}
                      {analyzedJd.industry && (
                        <span className="rounded-md bg-neutral-800 px-2 py-0.5 text-[10px] font-mono text-neutral-300">
                          {analyzedJd.industry}
                        </span>
                      )}
                    </p>
                  </div>
                  <span className="rounded-lg border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-bold text-purple-300 font-mono">
                    {analyzedJd.seniority_level || "MID"}
                  </span>
                </div>
              </div>

              {/* ATS Match Score Card */}
              {matchResult && (
                <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-purple-200">
                      <Target className="h-4 w-4 text-purple-400" />
                      Resume ↔ JD Compatibility Score
                    </div>
                    <div className="flex items-center gap-1.5 bg-purple-500/20 border border-purple-500/40 rounded-xl px-3 py-1 text-base font-extrabold text-purple-300 font-mono">
                      <Award className="h-4 w-4 text-amber-400" />
                      {matchResult.ats_score}% Match
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[10px] text-neutral-400 uppercase tracking-wider block font-bold mb-1.5 flex items-center gap-1 text-emerald-400">
                        <CheckCircle2 className="h-3 w-3" /> Matched Skills ({matchResult.matched_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {matchResult.matched_skills.map((s) => (
                          <span key={s} className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-medium">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] text-neutral-400 uppercase tracking-wider block font-bold mb-1.5 flex items-center gap-1 text-amber-400">
                        <AlertCircle className="h-3 w-3" /> Missing Target Skills ({matchResult.missing_skills.length})
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {matchResult.missing_skills.length > 0 ? (
                          matchResult.missing_skills.map((s) => (
                            <span key={s} className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-medium">
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-neutral-400 italic">No missing skills detected!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Required Skills Badges */}
              <div>
                <h4 className="text-xs font-bold text-neutral-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-blue-400" /> Required Skill Competencies
                </h4>
                <div className="flex flex-wrap gap-2">
                  {analyzedJd.required_skills && analyzedJd.required_skills.length > 0 ? (
                    analyzedJd.required_skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-300"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-neutral-500">General software engineering competencies parsed.</span>
                  )}
                </div>
              </div>

              {/* Start Tailored Interview CTA Button */}
              <div className="pt-4 border-t border-neutral-800 flex justify-end">
                <Button
                  onClick={() => navigate(`/interviews?resumeId=${selectedResumeId}&jdId=${analyzedJd.id}`)}
                  className="rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs py-3 px-6 flex items-center gap-2 shadow-lg shadow-indigo-600/30"
                >
                  <Play className="h-4 w-4" />
                  Start Tailored Multi-Agent Interview
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}