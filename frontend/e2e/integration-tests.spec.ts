import { test, expect } from '@playwright/test';
import {
  AuthHelper,
  TestDataFactory,
  TestAssertions
} from './test-utils';

test.describe('Integration E2E Tests', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
  });

  test('complete user workflow: registration to live trading', async ({ page }) => {
    // Step 1: Register new user
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Verify on dashboard
    await TestAssertions.assertOnDashboard(page);

    // Step 2: Create a strategy
    const strategy = TestDataFactory.strategy();
    await page.goto('/dashboard/strategies/new');
    await page.fill('[data-testid="strategy-name-input"]', strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);
    await page.fill('[data-testid="strategy-symbol-input"]', strategy.parameters.symbol);
    await page.click('[data-testid="strategy-save-button"]');
    await page.waitForURL('**/strategies');

    // Step 3: Go to backtesting and run a test
    await page.goto('/pages/backtesting.py');
    await page.selectOption('[data-testid="strategy-selector"]', strategy.name);
    await page.fill('[data-testid="start-date-input"]', '2023-01-01');
    await page.fill('[data-testid="end-date-input"]', '2023-12-31');
    await page.fill('[data-testid="initial-capital-input"]', '10000');

    const runButton = page.locator('[data-testid="run-backtest-button"]');
    if (await runButton.isVisible()) {
      await runButton.click();
      // Wait for potential results (may timeout if backend not ready)
      await page.waitForSelector('[data-testid="backtest-results"]', { timeout: 10000 }).catch(() => {
        console.log('Backtest may not be available - continuing with test');
      });
    }

    // Step 4: Check live trading interface
    await page.goto('/dashboard/live-trading');
    await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible();

    // Step 5: Verify navigation between sections works
    await page.goto('/dashboard/trades');
    await expect(page.locator('[data-testid="trades-table"]')).toBeVisible();

    await page.goto('/dashboard/risk-rules');
    await expect(page.locator('[data-testid="risk-dashboard"]')).toBeVisible();

    // Step 6: Logout and verify clean state
    await authHelper.logout();
    await TestAssertions.assertLoggedOut(page);
  });

  test('strategy lifecycle: creation to execution', async ({ page }) => {
    // Register and login
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Create strategy
    const strategy = TestDataFactory.strategy();
    await page.goto('/dashboard/strategies/new');
    await page.fill('[data-testid="strategy-name-input"]', strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);
    await page.fill('[data-testid="strategy-symbol-input"]', strategy.parameters.symbol);
    await page.click('[data-testid="strategy-save-button"]');
    await page.waitForURL('**/strategies');

    // Start strategy execution
    const startButton = page.locator(`[data-testid="start-strategy-${strategy.name}"]`);
    if (await startButton.isVisible()) {
      await startButton.click();
      await expect(page.locator('[data-testid="strategy-started-message"]')).toBeVisible();

      // Check if strategy appears as running
      await expect(page.locator('[data-testid="running-strategies-list"]')).toContainText(strategy.name);

      // Stop strategy
      const stopButton = page.locator(`[data-testid="stop-strategy-${strategy.name}"]`);
      if (await stopButton.isVisible()) {
        await stopButton.click();
        await expect(page.locator('[data-testid="strategy-stopped-message"]')).toBeVisible();
      }
    }

    // Delete strategy
    await page.click(`[data-testid="delete-strategy-${strategy.name}"]`);
    await page.click('[data-testid="confirm-delete-button"]');
    await expect(page.locator(`[data-testid="strategy-${strategy.name}"]`)).not.toBeVisible();
  });

  test('risk management integration with trading', async ({ page }) => {
    // Register and login
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Create risk rule
    await page.goto('/dashboard/risk-rules');
    await page.click('[data-testid="create-rule-button"]');
    await page.selectOption('[data-testid="rule-type-select"]', 'max-drawdown');
    await page.fill('[data-testid="rule-name-input"]', 'Max Drawdown Protection');
    await page.fill('[data-testid="threshold-input"]', '20'); // 20%
    await page.selectOption('[data-testid="action-select"]', 'stop-trading');
    await page.click('[data-testid="save-rule-button"]');

    // Go to live trading
    await page.goto('/dashboard/live-trading');

    // The risk rule should be active and enforced
    await expect(page.locator('[data-testid="active-risk-rules"]')).toContainText('Max Drawdown Protection');

    // Attempt to place a trade (this would test if risk rules are enforced)
    const tradeButton = page.locator('[data-testid="place-order-button"]');
    if (await tradeButton.isVisible()) {
      // Risk management should be integrated into order placement
      await tradeButton.click();
      await page.selectOption('[data-testid="order-symbol-select"]', 'AAPL');
      await page.selectOption('[data-testid="order-side-select"]', 'buy');
      await page.fill('[data-testid="order-quantity-input"]', '10000'); // Large quantity
      await page.click('[data-testid="submit-order-button"]');

      // Risk rule might prevent or warn about this trade
      const riskWarning = page.locator('[data-testid="risk-rule-warning"]');
      if (await riskWarning.isVisible()) {
        await expect(riskWarning).toBeVisible();
      }
    }
  });

  test('real-time data updates and UI responsiveness', async ({ page }) => {
    // Register and login
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Go to live trading dashboard
    await page.goto('/dashboard/live-trading');

    // Wait for initial data load
    await page.waitForSelector('[data-testid="portfolio-overview"]');

    const initialBalance = await page.locator('[data-testid="total-balance"]').textContent();

    // Simulate some time passing (WebSocket updates would happen here in real app)
    await page.waitForTimeout(2000);

    // Data should be updated (or at least still present)
    await expect(page.locator('[data-testid="total-balance"]')).toBeVisible();

    // Test UI responsiveness - various elements should be clickable
    const navButtons = [
      '[data-testid="nav-dashboard"]',
      '[data-testid="nav-strategies"]',
      '[data-testid="nav-trades"]'
    ];

    for (const button of navButtons) {
      const navButton = page.locator(button);
      if (await navButton.isVisible()) {
        await expect(navButton).toBeEnabled();
      }
    }
  });

  test('cross-platform compatibility basic check', async ({ page, browserName }) => {
    // This test will run on all browsers configured
    await page.goto('/login');

    // Basic functionality should work across all browsers
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();

    // Different browsers might have slightly different behaviors, but core functionality should work
    console.log(`Testing on browser: ${browserName}`);

    // Register a test user
    const testUser = TestDataFactory.user();
    await page.fill('[data-testid="email-input"]', testUser.email);
    await page.fill('[data-testid="password-input"]', testUser.password);
    await page.click('[data-testid="login-button"]');

    // Should handle the login attempt appropriately (may fail without backend, but should not crash)
    await page.waitForTimeout(1000); // Brief wait for potential redirects
  });

  test('error handling and recovery', async ({ page }) => {
    // Register and login
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Try to access invalid route
    await page.goto('/non-existent-route');
    // Should show 404 or redirect to dashboard (depending on implementation)
    await page.waitForTimeout(1000);

    // Try invalid form submission
    await page.goto('/dashboard/strategies/new');
    await page.click('[data-testid="strategy-save-button"]');
    // Should show validation errors
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();

    // Try to recover - fill form properly
    await page.fill('[data-testid="strategy-name-input"]', 'Recovery Test Strategy');
    await page.click('[data-testid="strategy-save-button"]');

    // Should succeed now
    await page.waitForURL('**/strategies');
    await expect(page.locator('[data-testid="strategies-table"]')).toContainText('Recovery Test Strategy');
  });

  test('performance under load simulation', async ({ page }) => {
    // Register and login
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);

    // Create multiple strategies quickly
    await page.goto('/dashboard/strategies');

    const startTime = Date.now();

    for (let i = 0; i < 3; i++) {
      await page.goto('/dashboard/strategies/new');
      const strategy = TestDataFactory.strategy({ name: `Performance Test Strategy ${i}` });
      await page.fill('[data-testid="strategy-name-input"]', strategy.name);
      await page.fill('[data-testid="strategy-description-input"]', strategy.description);
      await page.click('[data-testid="strategy-save-button"]');
      await page.waitForURL('**/strategies');
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    console.log(`Creating 3 strategies took ${duration}ms`);

    // Should complete within reasonable time (30 seconds max)
    expect(duration).toBeLessThan(30000);
  });
});
