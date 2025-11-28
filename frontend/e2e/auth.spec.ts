import { test } from '@playwright/test';
import {
  AuthHelper,
  TestDataFactory,
  TestAssertions,
  selectors
} from './test-utils';

test.describe('Authentication E2E Tests', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
  });

  test('should load login page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForSelector(selectors.loginForm);
    await TestAssertions.assertLoggedOut(page);
  });

  test('should load register page', async ({ page }) => {
    await page.goto('/register');
    await page.waitForSelector(selectors.registerForm);
  });

  test('should allow user registration and login', async ({ page }) => {
    // Create test user data
    const testUser = TestDataFactory.user();

    // Register new user
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Verify we're on dashboard after registration
    await TestAssertions.assertOnDashboard(page);

    // Logout
    await authHelper.logout();
    await TestAssertions.assertLoggedOut(page);

    // Login with same credentials
    await page.goto('/login');
    await authHelper.login(testUser.email, testUser.password);

    // Verify we're back on dashboard
    await TestAssertions.assertOnDashboard(page);
  });

  test('should handle invalid login credentials', async ({ page }) => {
    await page.goto('/login');

    // Try to login with invalid credentials
    await page.fill(selectors.emailInput, 'invalid@example.com');
    await page.fill(selectors.passwordInput, 'wrongpassword');
    await page.click(selectors.loginButton);

    // Should stay on login page and show error
    await TestAssertions.assertLoggedOut(page);
    await page.waitForSelector(selectors.errorMessage);
  });

  test('should prevent access to protected routes when not logged in', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');

    // Should redirect to login page
    await TestAssertions.assertLoggedOut(page);
  });

  test('should allow navigation between pages when authenticated', async ({ page }) => {
    const testUser = TestDataFactory.user();

    // Register and login
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Navigate to different sections of the app
    await page.goto('/dashboard/strategies');
    await page.waitForURL('**/strategies');

    await page.goto('/dashboard/trades');
    await page.waitForURL('**/trades');

    await page.goto('/dashboard/risk-rules');
    await page.waitForURL('**/risk-rules');
  });

  test('should maintain login state across page refreshes', async ({ page }) => {
    const testUser = TestDataFactory.user();

    // Register and login
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Refresh the page
    await page.reload();

    // Should still be logged in and on dashboard
    await TestAssertions.assertOnDashboard(page);
  });
});
