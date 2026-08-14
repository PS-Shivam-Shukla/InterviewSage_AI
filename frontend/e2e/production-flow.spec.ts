import { test, expect } from '@playwright/test';

test.describe('Production Release E2E Critical Path', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('interviewsage_access_token', 'mock-valid-e2e-token');
      window.localStorage.setItem('interviewsage_refresh_token', 'mock-valid-refresh-token');
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'usr-e2e-1',
          email: 'candidate@interviewsage.ai',
          full_name: 'E2E Candidate',
        }),
      });
    });

    await page.route('**/api/v1/resumes', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/interviews', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/reports', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });
  });

  test('Complete Navigation Path: Login -> Resumes -> Interviews -> Analytics -> Reports', async ({ page }) => {
    // 1. Login Page check
    await page.goto('/login');
    await expect(page).toHaveTitle(/InterviewSage AI/i);

    // 2. Resumes Page Navigation
    await page.goto('/resumes');
    await page.waitForLoadState('networkidle');

    // 3. Interviews Session Page Navigation
    await page.goto('/interviews');
    await page.waitForLoadState('networkidle');

    // 4. Analytics Page Navigation
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    // 5. Reports Page Navigation
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');
  });
});
