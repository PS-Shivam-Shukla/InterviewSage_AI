import { Resume, ResumeFilterOptions } from '../types/resume.types';

export function filterAndSortResumes(resumes: Resume[], options: ResumeFilterOptions): Resume[] {
  return resumes
    .filter((resume) => {
      // Search query filter
      if (options.searchQuery) {
        const query = options.searchQuery.toLowerCase();
        const matchesName = resume.file_path.toLowerCase().includes(query);
        const matchesSkill = resume.parsed_skills.some((s) => s.toLowerCase().includes(query));
        const matchesSeniority = resume.seniority_signal.toLowerCase().includes(query);
        if (!matchesName && !matchesSkill && !matchesSeniority) return false;
      }

      // Seniority filter
      if (options.seniority && options.seniority !== 'ALL') {
        if (resume.seniority_signal.toUpperCase() !== options.seniority.toUpperCase()) {
          return false;
        }
      }

      // Skill filter
      if (options.skillFilter && options.skillFilter !== 'ALL') {
        const hasSkill = resume.parsed_skills.some(
          (s) => s.toLowerCase() === options.skillFilter.toLowerCase()
        );
        if (!hasSkill) return false;
      }

      return true;
    })
    .sort((a, b) => {
      switch (options.sortBy) {
        case 'date_asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'name_asc':
          return a.file_path.localeCompare(b.file_path);
        case 'seniority':
          return a.seniority_signal.localeCompare(b.seniority_signal);
        case 'date_desc':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });
}

export function formatFileSize(bytes?: number): string {
  if (!bytes) return 'Unknown size';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getSeniorityBadgeVariant(seniority?: string): 'default' | 'success' | 'warning' | 'secondary' {
  switch (seniority?.toUpperCase()) {
    case 'STAFF':
    case 'PRINCIPAL':
    case 'ARCHITECT':
      return 'success';
    case 'SENIOR':
      return 'default';
    case 'MID':
      return 'warning';
    case 'JUNIOR':
    default:
      return 'secondary';
  }
}
