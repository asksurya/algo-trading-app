// frontend/src/app/dashboard/__tests__/page.test.tsx
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DashboardPage from '../page'

// Mock the useRouter hook
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

const queryClient = new QueryClient()

describe('DashboardPage', () => {
  it('renders the dashboard heading', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardPage />
      </QueryClientProvider>
    )
    const heading = screen.getByRole('heading', {
      name: /dashboard/i,
    })
    expect(heading).toBeInTheDocument()
  })
})
