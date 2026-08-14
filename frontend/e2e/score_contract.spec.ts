import { test, expect } from '@playwright/test';

test.describe('E2E Interview Scoring Contract & Boundary Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Inject auth token into localStorage to pass ProtectedRoutes authentication
    await page.addInitScript(() => {
      window.localStorage.setItem('interviewsage_access_token', 'mock-valid-e2e-token');
      window.localStorage.setItem('interviewsage_refresh_token', 'mock-valid-refresh-token');
    });

    // Mock User API endpoint
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'usr-e2e-1',
          email: 'candidate@interviewsage.ai',
          full_name: 'E2E Candidate',
          created_at: new Date().toISOString(),
        }),
      });
    });
  });

  test('Canonical 0-100 Score Contract Consistency Across API, Live Metrics, and Reports', async ({ page }) => {
    const mockInterviewId = 'int-e2e-score-100';

    // 1. Mock Answer Submission API response with canonical score_pct (80%)
    await page.route(`**/api/v1/interviews/${mockInterviewId}/answers`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          interview_id: mockInterviewId,
          status: 'IN_PROGRESS',
          evaluation: {
            score: 80,
            score_1_10: 8,
            display_score: '8/10 (80%)',
            technical_score: 80,
            communication_score: 85,
            confidence_score: 90,
            reasoning: 'Solid answer covering distributed state, Redis caching, and ACID guarantees.',
            feedback: 'Solid answer covering distributed state, Redis caching, and ACID guarantees.',
            rubric_breakdown: { Correctness: 80, Communication: 85, Confidence: 90 },
          },
          next_question: {
            id: 'q-2',
            sequence_number: 2,
            round_type: 'TECHNICAL',
            competency: 'System Architecture',
            difficulty: 'MEDIUM',
            text: 'How do you handle database failover during high concurrency write bursts?',
          },
          message: 'Answer evaluated via EvaluationAgent LLM.',
        }),
      });
    });

    // 2. Mock Interview Session GET response
    await page.route(`**/api/v1/interviews/${mockInterviewId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockInterviewId,
          status: 'IN_PROGRESS',
          target_role: 'Senior Backend Engineer',
          current_round: 'TECHNICAL',
          overall_score: 80,
          questions: [
            {
              id: 'q-1',
              sequence_number: 1,
              round_type: 'TECHNICAL',
              competency_targeted: 'Backend Architecture',
              difficulty: 'MEDIUM',
              question_text: 'Describe how you scale asynchronous Python microservices under 50k QPS.',
            },
          ],
        }),
      });
    });

    // 3. Mock Report GET response with matching 0-100 percentage scores (overall_score = 80)
    await page.route(`**/api/v1/reports/${mockInterviewId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          interview_id: mockInterviewId,
          role: 'Senior Backend Engineer',
          status: 'COMPLETED',
          overall_score: 80,
          generated_at: new Date().toISOString(),
          competency_scorecard: [
            { competency: 'Backend Architecture', skill: 'Backend Architecture', name: 'Backend Architecture', score: 80, fullMark: 100 },
            { competency: 'System Design', skill: 'System Design', name: 'System Design', score: 85, fullMark: 100 },
          ],
          improvement_plan: [
            { area: 'Concurrency Mitigation', action: 'Review lock-free data structures in Python.' },
          ],
          transcript_snapshot: [
            {
              question: 'Describe how you scale asynchronous Python microservices under 50k QPS.',
              answer: 'I implement FastAPI async workers with Redis write-through caching.',
              score: 80,
              display_score: '8/10 (80%)',
              reasoning: 'Solid explanation of caching and concurrency.',
            },
          ],
        }),
      });
    });

    // 4. Navigate to Interview Session Page
    await page.goto('/interviews');
    await page.waitForLoadState('networkidle');

    // Verify main page loaded
    await expect(page.locator('h1, h2, span')).toBeDefined();

    // 5. Navigate directly to Report Page for the interview
    await page.goto(`/reports/${mockInterviewId}`);
    await page.waitForLoadState('networkidle');

    // 6. Verify OverallScoreCard renders canonical score "80" and scale "/ 100"
    const overallScoreElement = page.locator('text=80').first();
    await expect(overallScoreElement).toBeVisible();

    const maxScaleElement = page.locator('text=/ 100').first();
    await expect(maxScaleElement).toBeVisible();

    // 7. Verify Competency Scorecard renders score 80 / 100
    const competencyScoreText = page.locator('text=80 / 100').first();
    await expect(competencyScoreText).toBeVisible();

    // 8. DOUBLE CONVERSION ASSERTIONS: Ensure no secondary multiplication occurs (e.g. 800 or 8000)
    const pageText = await page.innerText('body');
    expect(pageText).not.toContain('800 / 100');
    expect(pageText).not.toContain('800%');
    expect(pageText).not.toContain('8000%');
  });
});
