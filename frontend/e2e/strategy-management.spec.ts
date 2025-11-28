import { test, expect } from '@playwright/test';
import {
  AuthHelper,
  NavigationHelper,
  TestDataFactory,
  TestAssertions,
  selectors
} from './test-utils';

test.describe('Strategy Management E2E Tests', () => {
  let authHelper: AuthHelper;
  let navigationHelper: NavigationHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    navigationHelper = new NavigationHelper(page);

    // Login for all strategy tests
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);
  });

  test('should create a new strategy', async ({ page }) => {
    const strategy = TestDataFactory.strategy();

    // Navigate to create strategy page
    await page.goto('/dashboard/strategies/new');

    // Fill strategy form
    await page.fill(selectors.strategyNameInput, strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);

    // Configure strategy parameters
    await page.fill('[data-testid="strategy-symbol-input"]', strategy.parameters.symbol);
    await page.selectOption('[data-testid="strategy-timeframe-select"]', strategy.parameters.timeframe);

    // Add indicators
    for (const indicator of strategy.parameters.indicators) {
      await page.click(`[data-testid="indicator-${indicator}-checkbox"]`);
    }

    // Save strategy
    await page.click(selectors.strategySaveButton);

    // Verify strategy was created
    await page.waitForURL('**/strategies');
    await TestAssertions.assertStrategyCreated(page, strategy.name);
  });

  test('should edit existing strategy', async ({ page }) => {
    const strategy = TestDataFactory.strategy();
    const updatedName = `${strategy.name} Updated`;

    // First create a strategy
    await page.goto('/dashboard/strategies/new');
    await page.fill(selectors.strategyNameInput, strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);
    await page.click(selectors.strategySaveButton);
    await page.waitForURL('**/strategies');

    // Find and edit the strategy
    await page.click(`[data-testid="edit-strategy-${strategy.name}"]`);

    // Update strategy name
    await page.fill(selectors.strategyNameInput, updatedName);
    await page.click(selectors.strategySaveButton);

    // Verify strategy was updated
    await page.waitForURL('**/strategies');
    await TestAssertions.assertStrategyCreated(page, updatedName);
  });

  test('should delete strategy', async ({ page }) => {
    const strategy = TestDataFactory.strategy();

    // Create a strategy first
    await page.goto('/dashboard/strategies/new');
    await page.fill(selectors.strategyNameInput, strategy.name);
    await page.fill('[data-testid="strategy-description-input"]', strategy.description);
    await page.click(selectors.strategySaveButton);
    await page.waitForURL('**/strategies');

    // Delete the strategy
    await page.click(`[data-testid="delete-strategy-${strategy.name}"]`);
    await page.click('[data-testid="confirm-delete-button"]');

    // Verify strategy was deleted
    await page.waitForSelector(`[data-testid="strategy-${strategy.name}"]`, { state: 'hidden' });
  });

  test('should validate strategy form inputs', async ({ page }) => {
    await page.goto('/dashboard/strategies/new');

    // Try to save without name
    await page.click(selectors.strategySaveButton);

    // Should show validation error
    await page.waitForSelector('[data-testid="name-required-error"]');
    await expect(page.locator('[data-testid="name-required-error"]')).toBeVisible();

    // Fill name but leave other required fields empty
    await page.fill(selectors.strategyNameInput, 'Test Strategy');
    await page.click(selectors.strategySaveButton);

    // Should show other validation errors
    await page.waitForSelector('[data-testid="symbol-required-error"]');
  });

  test('should display strategy list correctly', async ({ page }) => {
    // Create multiple strategies
    const strategies = [
      TestDataFactory.strategy(),
      TestDataFactory.strategy(),
      TestDataFactory.strategy()
    ];

    for (const strategy of strategies) {
      await page.goto('/dashboard/strategies/new');
      await page.fill(selectors.strategyNameInput, strategy.name);
      await page.fill('[data-testid="strategy-description-input"]', strategy.description);
      await page.click(selectors.strategySaveButton);
      await page.waitForURL('**/strategies');
    }

    // Verify all strategies are displayed
    await page.goto('/dashboard/strategies');
    for (const strategy of strategies) {
      await expect(page.locator(selectors.strategiesTable)).toContainText(strategy.name);
    }
  });

  test('should filter strategies by status', async ({ page }) => {
    // Create strategies with different statuses
    const activeStrategy = TestDataFactory.strategy({ name: 'Active Strategy' });
    const inactiveStrategy = TestDataFactory.strategy({ name: 'Inactive Strategy' });

    // Create strategies and set their statuses
    await createStrategy(page, activeStrategy);
    await createStrategy(page, inactiveStrategy);

    // Filter by active strategies
    await page.selectOption('[data-testid="strategy-status-filter"]', 'active');
    await expect(page.locator(selectors.strategiesTable)).toContainText(activeStrategy.name);
    await expect(page.locator(selectors.strategiesTable)).not.toContainText(inactiveStrategy.name);

    // Filter by all strategies
    await page.selectOption('[data-testid="strategy-status-filter"]', 'all');
    await expect(page.locator(selectors.strategiesTable)).toContainText(activeStrategy.name);
    await expect(page.locator(selectors.strategiesTable)).toContainText(inactiveStrategy.name);
  });
});

async function createStrategy(page: any, strategy: any) {
  await page.goto('/dashboard/strategies/new');
  await page.fill(selectors.strategyNameInput, strategy.name);
  await page.fill('[data-testid="strategy-description-input"]', strategy.description);
  await page.fill('[data-testid="strategy-symbol-input"]', strategy.parameters.symbol);
  await page.click(selectors.strategySaveButton);
  await page.waitForURL('**/strategies');
}
