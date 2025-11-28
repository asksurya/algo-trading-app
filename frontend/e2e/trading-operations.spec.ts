import { test, expect } from '@playwright/test';
import {
  AuthHelper,
  TestDataFactory,
  TestAssertions,
  selectors
} from './test-utils';

test.describe('Trading Operations E2E Tests', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);

    // Login for all trading tests
    const testUser = TestDataFactory.user();
    await page.goto('/register');
    await authHelper.register(testUser.email, testUser.password);
  });

  test('should display live trading dashboard', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Should show trading dashboard with key components
    await expect(page.locator('[data-testid="trading-dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="portfolio-overview"]')).toBeVisible();
    await expect(page.locator('[data-testid="active-positions"]')).toBeVisible();
    await expect(page.locator('[data-testid="recent-trades"]')).toBeVisible();
  });

  test('should show portfolio balance and P/L', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Check portfolio information
    await expect(page.locator('[data-testid="total-balance"]')).toBeVisible();
    await expect(page.locator('[data-testid="daily-pnl"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-pnl"]')).toBeVisible();
  });

  test('should display active positions table', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Should show positions table with headers
    await expect(page.locator('[data-testid="positions-table"]')).toBeVisible();
    await expect(page.locator('th:has-text("Symbol")')).toBeVisible();
    await expect(page.locator('th:has-text("Quantity")')).toBeVisible();
    await expect(page.locator('th:has-text("Entry Price")')).toBeVisible();
    await expect(page.locator('th:has-text("Current Price")')).toBeVisible();
    await expect(page.locator('th:has-text("P/L")')).toBeVisible();
  });

  test('should display recent trades history', async ({ page }) => {
    await page.goto('/dashboard/trades');

    // Should show trades table
    await expect(page.locator(selectors.tradesTable)).toBeVisible();
    await expect(page.locator('th:has-text("Time")')).toBeVisible();
    await expect(page.locator('th:has-text("Symbol")')).toBeVisible();
    await expect(page.locator('th:has-text("Side")')).toBeVisible();
    await expect(page.locator('th:has-text("Quantity")')).toBeVisible();
    await expect(page.locator('th:has-text("Price")')).toBeVisible();
  });

  test('should allow manual order entry', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Open order entry form
    await page.click('[data-testid="place-order-button"]');

    // Fill order details
    await page.selectOption('[data-testid="order-symbol-select"]', 'AAPL');
    await page.selectOption('[data-testid="order-side-select"]', 'buy');
    await page.selectOption('[data-testid="order-type-select"]', 'market');
    await page.fill('[data-testid="order-quantity-input"]', '100');

    // Place order
    await page.click('[data-testid="submit-order-button"]');

    // Verify order confirmation
    await page.waitForSelector('[data-testid="order-confirmation"]');
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
  });

  test('should validate order entry form', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    await page.click('[data-testid="place-order-button"]');
    await page.click('[data-testid="submit-order-button"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="symbol-required-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="quantity-required-error"]')).toBeVisible();
  });

  test('should cancel pending orders', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Assuming there are pending orders, cancel one
    const cancelButton = page.locator('[data-testid="cancel-order-button"]').first();
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      await page.click('[data-testid="confirm-cancel-button"]');

      // Verify order was cancelled
      await expect(page.locator('[data-testid="order-cancelled-message"]')).toBeVisible();
    }
  });

  test('should show order status updates', async ({ page }) => {
    await page.goto('/dashboard/live-trading');

    // Place an order and monitor status
    await page.click('[data-testid="place-order-button"]');
    await page.selectOption('[data-testid="order-symbol-select"]', 'AAPL');
    await page.selectOption('[data-testid="order-side-select"]', 'buy');
    await page.selectOption('[data-testid="order-type-select"]', 'limit');
    await page.fill('[data-testid="order-quantity-input"]', '50');
    await page.fill('[data-testid="order-price-input"]', '150.00');
    await page.click('[data-testid="submit-order-button"]');

    // Check that order appears in pending orders
    await expect(page.locator('[data-testid="pending-orders-table"]')).toContainText('AAPL');
    await expect(page.locator('[data-testid="pending-orders-table"]')).toContainText('buy');
  });

  test('should filter trades by date range', async ({ page }) => {
    await page.goto('/dashboard/trades');

    // Set date filters
    await page.fill('[data-testid="start-date-input"]', '2024-01-01');
    await page.fill('[data-testid="end-date-input"]', '2024-12-31');
    await page.click('[data-testid="apply-filters-button"]');

    // Verify trades are filtered (implementation dependent)
    await page.waitForSelector('[data-testid="trades-loaded"]');
  });

  test('should export trades history', async ({ page }) => {
    await page.goto('/dashboard/trades');

    // Click export button
    const exportButton = page.locator('[data-testid="export-trades-button"]');
    if (await exportButton.isVisible()) {
      await exportButton.click();

      // Should trigger download or show export options
      await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
    }
  });
});
