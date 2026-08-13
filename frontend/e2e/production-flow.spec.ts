import { test, expect } from '@playwright/test';

test.describe('Production Release E2E Critical Path', () => {
  test('Complete Flow: Login -> Resume -> Interview Setup -> Live Interview -> Transcript -> Analytics', async ({
    page,
  }) => {
    // 1. Navigate to Login Page
    await page.goto('/login');
    await expect(page).toHaveTitle(/InterviewSage AI/i);

    // 2. Fill authentication credentials & submit
    await page.fill('input[type="email"]', 'candidate@interviewsage.ai');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // 3. Navigate to Resume Intelligence Hub
    await page.goto('/resumes');
    await expect(page.locator('h1')).toContainText(/Resume Intelligence/i);

    // 4. Navigate to Interview Setup
    await page.goto('/interviews/setup');
    await expect(page.locator('h1')).toContainText(/Interview Setup/i);

    // 5. Select Job Role & Start Interview Session
    await page.fill('input[label="Target Company Name"]', 'InterviewSage Enterprise');
    await page.click('button:has-text("Start AI Interview Session")');

    // 6. Live Interview Session Page Verification
    await page.waitForURL(/\/interviews\/.*\/voice|\/interviews\/.*\/session/);
    await expect(page.locator('text=InterviewSage AI')).toBeVisible();

    // 7. Verify Transcript Export Options
    await expect(page.locator('button:has-text("TXT")')).toBeVisible();
    await expect(page.locator('button:has-text(".MD")')).toBeVisible();

    // 8. End Session & Navigate to Analytics
    await page.click('button:has-text("End Session")');
    await page.click('button:has-text("End & Save Results")');
    await page.click('button:has-text("View Analytics")');

    // 9. Post-Interview Analytics Verification
    await expect(page.locator('h1')).toContainText(/Analytics & Replay/i);
    await expect(page.locator('text=Technical Score')).toBeVisible();
  });
});
