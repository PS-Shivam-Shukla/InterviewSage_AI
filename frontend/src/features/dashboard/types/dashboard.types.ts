export interface ExecutiveMetrics {
  totalInterviews: number;
  activeInterviews: number;
  completedInterviews: number;
  successRate: number;
  avgDurationMinutes: number;
  avgAtsScore: number;
  avgTechnicalScore: number;
  avgCommunicationScore: number;
  avgHiringProbability: number;
  activeCandidates: number;
}

export interface HeatmapPoint {
  day: string;
  hour: number;
  value: number;
}

export interface QuestionDistributionItem {
  category: string;
  count: number;
  avgScore: number;
}
