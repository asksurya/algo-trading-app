import { Page, BrowserContext } from '@playwright/test';
import { expect } from '@playwright/test';

/**
 * Test utilities for E2E testing
 */

// Common test selectors
export const selectors = {
  // Authentication
  loginForm: '[data-testid="login-form"]',
  registerForm: '[data-testid="register-form"]',
  emailInput: '[data-testid="email-input"]',
  passwordInput: '[data-testid="password-input"]',
  loginButton: '[data-testid="login-button"]',
  registerButton: '[data-testid="register-button"]',
  logoutButton: '[data-testid="logout-button"]',

  // Dashboard
  dashboard: '[data-testid="dashboard"]',
  strategiesTable: '[data-testid="strategies-table"]',
  tradesTable: '[data-testid="trades-table"]',
  createStrategyButton: '[data-testid="create-strategy-button"]',
  backtestButton: '[data-testid="backtest-button"]',

  // Strategy Management
  strategyForm: '[data-testid="strategy-form"]',
  strategyNameInput: '[data-testid="strategy-name-input"]',
  strategySaveButton: '[data-testid="strategy-save-button"]',
  strategyDeleteButton: '[data-testid="strategy-delete-button"]',

  // Navigation
  navDashboard: '[data-testid="nav-dashboard"]',
  navStrategies: '[data-testid="nav-strategies"]',
  navTrades: '[data-testid="nav-trades"]',
  navSettings: '[data-testid="nav-settings"]',

  // Loading and States
  loadingSpinner: '[data-testid="loading-spinner"]',
  errorMessage: '[data-testid="error-message"]',
  successMessage: '[data-testid="success-message"]',
};

/**
 * Authentication helpers
 */
export class AuthHelper {
  constructor(private page: Page) {}

  async login(email: string, password: string) {
    await this.page.fill(selectors.emailInput, email);
    await this.page.fill(selectors.passwordInput, password);
    await this.page.click(selectors.loginButton);
    await this.page.waitForURL('**/dashboard');
  }

  async register(email: string, password: string) {
    await this.page.fill(selectors.emailInput, email);
    await this.page.fill(selectors.passwordInput, password);
    await this.page.click(selectors.registerButton);
    await this.page.waitForURL('**/dashboard');
  }

  async logout() {
    await this.page.click(selectors.logoutButton);
    await this.page.waitForURL('**/login');
  }

  async isLoggedIn(): Promise<boolean> {
    return this.page.url().includes('/dashboard');
  }
}

/**
 * Navigation helpers
 */
export class NavigationHelper {
  constructor(private page: Page) {}

  async goToDashboard() {
    await this.page.click(selectors.navDashboard);
    await this.page.waitForURL('**/dashboard');
  }

  async goToStrategies() {
    await this.page.click(selectors.navStrategies);
    await this.page.waitForURL('**/strategies');
  }

  async goToTrades() {
    await this.page.click(selectors.navTrades);
    await this.page.waitForURL('**/trades');
  }

  async goToSettings() {
    await this.page.click(selectors.navSettings);
    await this.page.waitForURL('**/settings');
  }
}

/**
 * API helpers for direct backend calls
 */
export class APIHelper {
  constructor(private context: BrowserContext) {}

  async createTestUser(email: string, password: string) {
    const response = await this.context.request.post('http://localhost:8000/api/v1/auth/register', {
      data: { email, password }
    });
    return response.json();
  }

  async deleteTestUser(userId: string) {
    const response = await this.context.request.delete(`http://localhost:8000/api/v1/auth/users/${userId}`);
    return response.ok();
  }

  async getAuthToken(email: string, password: string) {
    const response = await this.context.request.post('http://localhost:8000/api/v1/auth/login', {
      data: { email, password }
    });
    const data = await response.json();
    return data.access_token;
  }
}

/**
 * Page object helpers
 */
export class PageHelper {
  constructor(private page: Page) {}

  async waitForLoading() {
    await this.page.waitForSelector(selectors.loadingSpinner, { state: 'hidden', timeout: 10000 });
  }

  async waitForError() {
    await this.page.waitForSelector(selectors.errorMessage, { timeout: 5000 });
  }

  async waitForSuccess() {
    await this.page.waitForSelector(selectors.successMessage, { timeout: 5000 });
  }

  async getErrorMessage(): Promise<string | null> {
    return this.page.locator(selectors.errorMessage).textContent();
  }

  async getSuccessMessage(): Promise<string | null> {
    return this.page.locator(selectors.successMessage).textContent();
  }
}

/**
 * Test data factories
 */
export const TestDataFactory = {
  user: (overrides = {}) => ({
    email: `test-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    ...overrides
  }),

  strategy: (overrides = {}) => ({
    name: `Test Strategy ${Date.now()}`,
    description: 'Test strategy for E2E testing',
    parameters: {
      symbol: 'AAPL',
      timeframe: '1d',
      indicators: ['SMA', 'RSI']
    },
    ...overrides
  })
};

/**
 * Common test assertions
 */
export const TestAssertions = {
  async assertOnDashboard(page: Page) {
    await expect(page).toHaveURL(/.*\/dashboard/);
    await expect(page.locator(selectors.dashboard)).toBeVisible();
  },

  async assertLoggedOut(page: Page) {
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator(selectors.loginForm)).toBeVisible();
  },

  async assertStrategyCreated(page: Page, strategyName: string) {
    await expect(page.locator(selectors.strategiesTable)).toContainText(strategyName);
  },

  async assertErrorMessage(page: Page, message: string) {
    await expect(page.locator(selectors.errorMessage)).toContainText(message);
  },

  async assertSuccessMessage(page: Page, message: string) {
    await expect(page.locator(selectors.successMessage)).toContainText(message);
  }
};
