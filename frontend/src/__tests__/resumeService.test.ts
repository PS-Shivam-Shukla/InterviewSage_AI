import { describe, it, expect } from 'vitest';
import { resumeService } from '../features/resume/services/resume.service';

describe('resumeService Unit Tests', () => {
  it('should have required service API methods', () => {
    expect(typeof resumeService.uploadResume).toBe('function');
    expect(typeof resumeService.listResumes).toBe('function');
    expect(typeof resumeService.getResume).toBe('function');
    expect(typeof resumeService.deleteResume).toBe('function');
    expect(typeof resumeService.replaceResume).toBe('function');
    expect(typeof resumeService.getResumeAnalysis).toBe('function');
    expect(typeof resumeService.downloadResumeText).toBe('function');
  });
});
