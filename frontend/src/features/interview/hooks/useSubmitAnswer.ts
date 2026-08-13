import { useMutation, useQueryClient } from '@tanstack/react-query';
import { interviewService } from '../services/interview.service';
import { SubmitAnswerPayload } from '../types/interview.types';
import { useInterviewStore } from '../store/InterviewStore';

export function useSubmitAnswer() {
  const queryClient = useQueryClient();

  return useMutation<any, Error, SubmitAnswerPayload>({
    mutationFn: (payload) => interviewService.submitAnswer(payload),
    onSuccess: (data, variables) => {
      if (data?.evaluation) {
        const ev = data.evaluation;
        const { addTranscriptEntry, updateMetrics } = useInterviewStore.getState();

        // Use actual LLM scores — no hardcoded fallbacks like 88/90/92
        const evalScore = typeof ev.score === 'number' ? ev.score : 0;

        updateMetrics({
          answerQualityScore: evalScore,
          technicalScore: typeof ev.technical_coverage === 'number' ? ev.technical_coverage : evalScore,
          communicationScore: typeof ev.communication_score === 'number' ? ev.communication_score : evalScore,
          confidenceScore: typeof ev.confidence_score === 'number' ? ev.confidence_score : evalScore,
        });

        addTranscriptEntry({
          id: `cand-${Date.now()}`,
          speaker: 'CANDIDATE',
          text: variables.answer,
          timestamp: new Date().toISOString(),
        });

        if (ev.reasoning || ev.feedback) {
          addTranscriptEntry({
            id: `eval-${Date.now()}`,
            speaker: 'AI',
            text: ev.reasoning || ev.feedback,
            timestamp: new Date().toISOString(),
            feedback: {
              technical_score: typeof ev.technical_coverage === 'number' ? ev.technical_coverage : evalScore,
              communication_score: typeof ev.communication_score === 'number' ? ev.communication_score : evalScore,
              confidence_score: typeof ev.confidence_score === 'number' ? ev.confidence_score : evalScore,
            },
          });
        }
      }

      queryClient.invalidateQueries({ queryKey: ['interview', variables.interview_id] });
      queryClient.invalidateQueries({ queryKey: ['transcripts', variables.interview_id] });
    },
  });
}
