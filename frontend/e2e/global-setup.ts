import { request } from '@playwright/test';

async function globalSetup() {
  console.log('Starting E2E test environment setup...');

  // Create a request context for API calls
  const requestContext = await request.newContext();

  // Clean up any existing test data
  try {
    // Clean up test users
    await requestContext.delete('http://localhost:8000/api/v1/auth/users/test-cleanup');

    // Clean up test strategies
    await requestContext.delete('http://localhost:8000/api/v1/strategies/test-cleanup');

    // Clean up test trades
    await requestContext.delete('http://localhost:8000/api/v1/trades/test-cleanup');

    console.log('Test data cleanup completed');
  } catch (error) {
    console.warn('Test data cleanup failed, continuing:', error);
  }

  // Verify backend is running
  try {
    const response = await requestContext.get('http://localhost:8000/api/v1/health');
    if (!response.ok()) {
      throw new Error(`Backend health check failed: ${response.status()}`);
    }
    console.log('Backend is healthy and running');
  } catch (error) {
    console.error('Backend is not available:', error);
    throw error;
  } finally {
    await requestContext.dispose();
  }

  console.log('E2E test environment setup completed');
}

export default globalSetup;
