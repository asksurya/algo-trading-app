# E2E Test Baseline Document

**Date**: 2024-12-24
**Status**: Pre-implementation baseline

## Current State

The frontend application has several missing `/lib/` files that prevent the application from building successfully. These missing files cause immediate module resolution errors when the Next.js dev server starts.

## Missing Files Identified

1. **`@/lib/stores/auth-store`** - Required by login and register pages
2. **`@/lib/utils`** - Required by multiple UI components
3. **`@/lib/api/query-client`** - Required by providers.tsx
4. **`@/lib/hooks/use-broker`** - Required by dashboard page
5. **`@/lib/hooks/use-strategies`** - Required by strategies page
6. **`@/lib/hooks/use-trades`** - Required by trades page
7. **`@/lib/hooks/use-backtests`** - Required by backtests page
8. **`@/lib/api/live-trading`** - Required by live-trading pages
9. **`@/lib/api/optimizer`** - Required by optimizer page
10. **`@/lib/api/strategies`** - Required by optimizer page

## Smoke Test Results (Pre-implementation)

| Test | Status | Reason |
|------|--------|--------|
| Homepage loads | ✓ Pass | Static page renders |
| Login page accessible | ✗ Fail | Module not found: @/lib/stores/auth-store |
| Register page accessible | ✗ Fail | Module not found: @/lib/stores/auth-store |
| Unauthenticated redirects | ✗ Fail | Page compilation fails |
| Login form fields | ✗ Fail | Page compilation fails |
| Register form fields | ✗ Fail | Page compilation fails |
| Login -> Register link | ✗ Fail | Page compilation fails |
| Register -> Login link | ✗ Fail | Page compilation fails |

**Result: 1 passed, 7 failed**

## Error Log

```
Module not found: Can't resolve '@/lib/stores/auth-store'
  > 10 | import { useAuthStore, AuthState } from "@/lib/stores/auth-store";
```

## Expected State After Implementation

After completing Phases 1-4 of the TDD implementation plan:
- All smoke tests should pass
- Login and register pages should render
- Dashboard should be accessible after authentication
- All missing hooks and API clients should be available

## Existing E2E Tests

The following E2E test files already exist and will need to pass after implementation:
- `auth.spec.ts` - Authentication flow tests
- `strategy-management.spec.ts` - Strategy CRUD operations
- `backtesting.spec.ts` - Backtest creation and viewing
- `trading-operations.spec.ts` - Trade execution tests
- `risk-management.spec.ts` - Risk rule tests
- `integration-tests.spec.ts` - Full integration scenarios

## Files That Exist

The following `/lib/` files already exist and can serve as patterns:
- `frontend/src/lib/api/execution.ts` - API client pattern
- `frontend/src/lib/hooks/use-execution.ts` - React Query hook pattern

## Notes

This baseline documents the state before any implementation changes. After each phase is completed, tests should be re-run to verify progress.
