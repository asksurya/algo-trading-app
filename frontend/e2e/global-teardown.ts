import { request } from '@playwright/test';

async function globalTeardown() {
  console.log('Starting E2E test environment teardown...');

  // Create a request context for API calls
  const requestContext = await request.newContext();

  try {
    // Final cleanup of test data
    await requestContext.delete('http://localhost:8000/api/v1/auth/users/test-cleanup-final');
    await requestContext.delete('http://localhost:8000/api/v1/strategies/test-cleanup-final');
    await requestContext.delete('http://localhost:8000/api/v1/trades/test-cleanup-final');

    console.log('Final test data cleanup completed');
  } catch (error) {
    console.warn('Final test data cleanup failed:', error);
  } finally {
    await requestContext.dispose();
  }

  console.log('E2E test environment teardown completed');
}

export default globalTeardown;
