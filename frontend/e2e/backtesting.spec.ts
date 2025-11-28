import { test, expect } from '@playwright/test';
import {
  AuthHelper,
  TestDataFactory,
  TestAssertions
} from './test-utils';

test.describe('Backtesting E2E Tests', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);

    // Login for all backtesting tests
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);
  });

  test('should load backtesting dashboard', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Should show backtesting interface
    await expect(page.locator('[data-testid="backtesting-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="strategy-selector"]')).toBeVisible();
  });

  test('should run backtest with basic parameters', async ({ page }) => {
    // Create a strategy first
    const strategy = TestDataFactory.strategy();
    await page.goto('/dashboard/strategies/new');
    await page.fill('[data-testid="strategy-name-input"]', strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);
    await page.fill('[data-testid="strategy-symbol-input"]', strategy.parameters.symbol);
    await page.click('[data-testid="strategy-save-button"]');
    await page.waitForURL('**/strategies');

    // Now go to backtesting
    await page.goto('/pages/backtesting.py');

    // Select strategy
    await page.selectOption('[data-testid="strategy-selector"]', strategy.name);

    // Set backtest parameters
    await page.fill('[data-testid="start-date-input"]', '2023-01-01');
    await page.fill('[data-testid="end-date-input"]', '2023-12-31');
    await page.fill('[data-testid="initial-capital-input"]', '10000');

    // Run backtest
    await page.click('[data-testid="run-backtest-button"]');

    // Wait for results
    await page.waitForSelector('[data-testid="backtest-results"]', { timeout: 30000 });

    // Verify results are displayed
    await expect(page.locator('[data-testid="total-return"]')).toBeVisible();
    await expect(page.locator('[data-testid="sharpe-ratio"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-drawdown"]')).toBeVisible();
  });

  test('should show backtest performance charts', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Run a backtest first (assuming one exists or create one)
    await page.selectOption('[data-testid="strategy-selector"]', 'Any Available Strategy');
    await page.click('[data-testid="run-backtest-button"]');

    // Should show various charts
    await expect(page.locator('[data-testid="equity-curve-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="returns-distribution-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="drawdown-chart"]')).toBeVisible();
  });

  test('should display trade-by-trade breakdown', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Run backtest and navigate to trades tab
    await page.click('[data-testid="run-backtest-button"]');
    await page.waitForSelector('[data-testid="backtest-results"]');
    await page.click('[data-testid="trades-tab"]');

    // Should show detailed trade list
    await expect(page.locator('[data-testid="trades-breakdown-table"]')).toBeVisible();
    await expect(page.locator('th:has-text("Entry Date")')).toBeVisible();
    await expect(page.locator('th:has-text("Exit Date")')).toBeVisible();
    await expect(page.locator('th:has-text("Profit/Loss")')).toBeVisible();
  });

  test('should allow parameter optimization', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Select strategy and enable optimization
    await page.selectOption('[data-testid="strategy-selector"]', 'Any Strategy');
    await page.click('[data-testid="enable-optimization-checkbox"]');

    // Set optimization parameters
    await page.fill('[data-testid="param1-min-input"]', '10');
    await page.fill('[data-testid="param1-max-input"]', '50');
    await page.fill('[data-testid="param1-step-input"]', '5');

    // Run optimization
    await page.click('[data-testid="optimize-button"]');

    // Should show optimization results
    await page.waitForSelector('[data-testid="optimization-results"]');
    await expect(page.locator('[data-testid="best-parameters"]')).toBeVisible();
    await expect(page.locator('[data-testid="parameter-heatmap"]')).toBeVisible();
  });

  test('should handle invalid backtest parameters', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Try to run without required parameters
    await page.click('[data-testid="run-backtest-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="strategy-required-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="date-range-required-error"]')).toBeVisible();
  });

  test('should save and load backtest configurations', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Set up backtest parameters
    await page.selectOption('[data-testid="strategy-selector"]', 'Test Strategy');
    await page.fill('[data-testid="start-date-input"]', '2023-01-01');
    await page.fill('[data-testid="end-date-input"]', '2023-12-31');

    // Save configuration
    await page.fill('[data-testid="config-name-input"]', 'My Test Config');
    await page.click('[data-testid="save-config-button"]');

    await expect(page.locator('[data-testid="config-saved-message"]')).toBeVisible();

    // Load configuration
    await page.selectOption('[data-testid="load-config-select"]', 'My Test Config');
    await page.click('[data-testid="load-config-button"]');

    // Verify parameters are loaded
    await expect(page.locator('[data-testid="start-date-input"]')).toHaveValue('2023-01-01');
    await expect(page.locator('[data-testid="end-date-input"]')).toHaveValue('2023-12-31');
  });

  test('should export backtest results', async ({ page }) => {
    await page.goto('/pages/backtesting.py');

    // Run a backtest
    await page.click('[data-testid="run-backtest-button"]');
    await page.waitForSelector('[data-testid="backtest-results"]');

    // Export results
    const exportButton = page.locator('[data-testid="export-results-button"]');
    if (await exportButton.isVisible()) {
      await exportButton.click();

      // Should show export options or trigger download
      await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    }
  });
});
