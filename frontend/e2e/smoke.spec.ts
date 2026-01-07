import { test, expect } from '@playwright/test';

/**
 * Smoke Tests - Baseline
 * These tests establish the baseline functionality before implementing missing features.
 * They verify that core navigation and authentication flows work properly.
 */
test.describe('Smoke Tests - Baseline', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');
    // The page should load without errors
    await expect(page).toHaveURL(/\//);
  });

  test('login page accessible', async ({ page }) => {
    await page.goto('/login');
    // Login page should have a login button or form
    await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible();
  });

  test('register page accessible', async ({ page }) => {
    await page.goto('/register');
    // Register page should have a register/sign up button
    await expect(page.getByRole('button', { name: /register|sign up|create/i })).toBeVisible();
  });

  test('unauthenticated redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    // Should redirect to login page when not authenticated
    await expect(page).toHaveURL(/login/);
  });

  test('login form has required fields', async ({ page }) => {
    await page.goto('/login');

    // Should have email and password fields
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });

  test('register form has required fields', async ({ page }) => {
    await page.goto('/register');

    // Should have email and password fields at minimum
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });

  test('login page has link to register', async ({ page }) => {
    await page.goto('/login');

    // Should have a link to register/sign up
    await expect(page.getByRole('link', { name: /register|sign up|create account/i })).toBeVisible();
  });

  test('register page has link to login', async ({ page }) => {
    await page.goto('/register');

    // Should have a link to login/sign in
    await expect(page.getByRole('link', { name: /login|sign in/i })).toBeVisible();
  });
});
