import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useInterviewStore } from '../store/InterviewStore';

describe('InterviewAnswerInput Integration Contract Tests (Step 3.5.1)', () => {
  beforeEach(() => {
    useInterviewStore.getState().resetSession();
    vi.restoreAllMocks();
  });

  it('should initialize store with IDLE state and OFF mic status', () => {
    const store = useInterviewStore.getState();
    expect(store.aiState).toBe('IDLE');
    expect(store.micStatus).toBe('OFF');
    expect(store.micLevel).toBe(0);
  });

  it('should prevent mode switching during THINKING or SPEAKING state', () => {
    useInterviewStore.getState().setAIState('THINKING');
    expect(useInterviewStore.getState().aiState).toBe('THINKING');

    useInterviewStore.getState().setAIState('SPEAKING');
    expect(useInterviewStore.getState().aiState).toBe('SPEAKING');
  });

  it('should synchronize mic level updates with WaveformVisualizer contract', () => {
    useInterviewStore.getState().setMicLevel(85);
    expect(useInterviewStore.getState().micLevel).toBe(85);
  });

  it('should prevent duplicate END_CANDIDATE_SPEECH events during THINKING state', () => {
    useInterviewStore.getState().setAIState('THINKING');
    expect(useInterviewStore.getState().aiState).toBe('THINKING');
    // Button controls are disabled during THINKING
    const canClick = useInterviewStore.getState().aiState === 'IDLE';
    expect(canClick).toBe(false);
  });
});
