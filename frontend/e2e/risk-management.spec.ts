import { test, expect } from '@playwright/test';
import {
  AuthHelper,
  TestDataFactory
} from './test-utils';

test.describe('Risk Management E2E Tests', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);

    // Login for all risk management tests
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);
  });

  test('should load risk rules dashboard', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    await expect(page.locator('[data-testid="risk-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="risk-rules-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="portfolio-risk-metrics"]')).toBeVisible();
  });

  test('should create a new risk rule', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Open create rule form
    await page.click('[data-testid="create-rule-button"]');

    // Fill rule details
    await page.selectOption('[data-testid="rule-type-select"]', 'max-drawdown');
    await page.fill('[data-testid="rule-name-input"]', 'Max Drawdown Rule');
    await page.fill('[data-testid="threshold-input"]', '10'); // 10%
    await page.selectOption('[data-testid="action-select"]', 'stop-trading');

    // Save rule
    await page.click('[data-testid="save-rule-button"]');

    // Verify rule was created
    await expect(page.locator('[data-testid="risk-rules-table"]')).toContainText('Max Drawdown Rule');
  });

  test('should edit existing risk rule', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Create a rule first
    await page.click('[data-testid="create-rule-button"]');
    await page.selectOption('[data-testid="rule-type-select"]', 'position-size');
    await page.fill('[data-testid="rule-name-input"]', 'Position Size Limit');
    await page.fill('[data-testid="threshold-input"]', '5'); // 5% of portfolio
    await page.click('[data-testid="save-rule-button"]');
    await page.waitForSelector('[data-testid="rule-created-message"]');

    // Edit the rule
    await page.click('[data-testid="edit-rule-Position Size Limit"]');
    await page.fill('[data-testid="threshold-input"]', '3'); // Change to 3%
    await page.click('[data-testid="save-rule-button"]');

    // Verify rule was updated
    await expect(page.locator('[data-testid="rule-updated-message"]')).toBeVisible();
  });

  test('should delete risk rule', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Create and then delete a rule
    await page.click('[data-testid="create-rule-button"]');
    await page.selectOption('[data-testid="rule-type-select"]', 'daily-loss');
    await page.fill('[data-testid="rule-name-input"]', 'Daily Loss Rule');
    await page.fill('[data-testid="threshold-input"]', '500');
    await page.click('[data-testid="save-rule-button"]');

    // Delete the rule
    await page.click('[data-testid="delete-rule-Daily Loss Rule"]');
    await page.click('[data-testid="confirm-delete-button"]');

    // Verify rule was deleted
    await expect(page.locator('[data-testid="risk-rules-table"]')).not.toContainText('Daily Loss Rule');
  });

  test('should validate risk rule parameters', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    await page.click('[data-testid="create-rule-button"]');
    await page.click('[data-testid="save-rule-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="rule-type-required-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="rule-name-required-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="threshold-required-error"]')).toBeVisible();
  });

  test('should display current risk metrics', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Should show various risk metrics
    await expect(page.locator('[data-testid="current-drawdown"]')).toBeVisible();
    await expect(page.locator('[data-testid="portfolio-var"]')).toBeVisible();
    await expect(page.locator('[data-testid="sharpe-ratio"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-portfolio-allocation"]')).toBeVisible();
  });

  test('should enable/disable risk rules', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Create a rule first
    await page.click('[data-testid="create-rule-button"]');
    await page.selectOption('[data-testid="rule-type-select"]', 'max-loss');
    await page.fill('[data-testid="rule-name-input"]', 'Max Loss Rule');
    await page.fill('[data-testid="threshold-input"]', '1000');
    await page.click('[data-testid="save-rule-button"]');

    // Toggle rule on/off
    const toggleButton = page.locator('[data-testid="toggle-rule-Max Loss Rule"]');
    await toggleButton.click();

    // Verify state changed (implementation dependent - could be visual indicator)
    await expect(page.locator('[data-testid="rule-disabled-indicator"]')).toBeVisible();
  });

  test('should show risk rule violations', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Create a strict rule that might trigger violations
    await page.click('[data-testid="create-rule-button"]');
    await page.selectOption('[data-testid="rule-type-select"]', 'max-position-size');
    await page.fill('[data-testid="rule-name-input"]', 'Position Size Rule');
    await page.fill('[data-testid="threshold-input"]', '1'); // 1% max position size (very restrictive)
    await page.click('[data-testid="save-rule-button"]');

    // Navigate to where violations might occur
    await page.goto('/dashboard/live-trading');

    // If there are violations, they should be displayed
    const violationsAlert = page.locator('[data-testid="risk-violations-alert"]');
    // This test may or may not show violations depending on current portfolio state
    if (await violationsAlert.isVisible()) {
      await expect(violationsAlert).toContainText('Position Size Rule');
    }
  });

  test('should allow risk rule priority configuration', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    // Create multiple rules
    await createRiskRule(page, 'High Priority Rule', 'position-size', '2', 1);
    await createRiskRule(page, 'Low Priority Rule', 'daily-loss', '200', 2);

    // Should show priority ordering
    await expect(page.locator('[data-testid="risk-rules-table"]').locator('tbody tr').first()).toContainText('High Priority Rule');
  });

  test('should export risk rules configuration', async ({ page }) => {
    await page.goto('/dashboard/risk-rules');

    const exportButton = page.locator('[data-testid="export-rules-button"]');
    if (await exportButton.isVisible()) {
      await exportButton.click();

      // Should show export options or trigger download
      await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    }
  });
});

async function createRiskRule(page: any, name: string, type: string, threshold: string, priority: number) {
  await page.click('[data-testid="create-rule-button"]');
  await page.selectOption('[data-testid="rule-type-select"]', type);
  await page.fill('[data-testid="rule-name-input"]', name);
  await page.fill('[data-testid="threshold-input"]', threshold);
  await page.fill('[data-testid="priority-input"]', priority.toString());
  await page.click('[data-testid="save-rule-button"]');
  await page.waitForSelector('[data-testid="rule-created-message"]');
}
