import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import PortfolioPage from '../page'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}))

const mockSummary = {
  total_equity: 100000.0,
  cash_balance: 50000.0,
  positions_value: 50000.0,
  daily_pnl: 500.0,
  daily_return_pct: 0.5,
  total_pnl: 15000.0,
  total_return_pct: 15.0,
  num_positions: 5,
  num_long_positions: 4,
  num_short_positions: 1,
  last_updated: '2024-12-25T10:00:00Z',
}

const mockMetrics = {
  period: 'monthly',
  total_return_pct: 15.0,
  annualized_return: 0.18,
  sharpe_ratio: 1.8,
  sortino_ratio: 2.1,
  max_drawdown_pct: -8.5,
  win_rate: 62.0,
  profit_factor: 2.3,
}

const mockMetricsWithNulls = {
  period: 'daily',
  total_return_pct: 0.5,
  annualized_return: null,
  sharpe_ratio: null,
  sortino_ratio: null,
  max_drawdown_pct: null,
  win_rate: null,
  profit_factor: null,
}

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

const renderComponent = (queryClient = createQueryClient()) => {
  return render(
    <QueryClientProvider client={queryClient}>
      <PortfolioPage />
    </QueryClientProvider>
  )
}

describe('PortfolioPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.setItem('token', 'test-token')
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('Loading State', () => {
    it('renders loading state initially', () => {
      // Mock fetch to never resolve (simulate loading)
      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      )

      renderComponent()

      expect(screen.getByText(/loading portfolio analytics/i)).toBeInTheDocument()
      const spinner = screen.getByRole('heading', { name: /portfolio analytics/i })
        .closest('div')
        .querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('shows loading spinner while fetching data', () => {
      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      )

      renderComponent()

      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
      expect(spinner).toHaveClass('border-b-2', 'border-blue-600')
    })
  })

  describe('Summary Cards', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('renders summary cards with correct data', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total equity/i)).toBeInTheDocument()
      })

      expect(screen.getByText('$100,000.00')).toBeInTheDocument()
      expect(screen.getByText(/cash: \$50,000.00/i)).toBeInTheDocument()
    })

    it('renders daily P&L card with correct formatting', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/daily p&l/i)).toBeInTheDocument()
      })

      expect(screen.getByText('$500.00')).toBeInTheDocument()
      expect(screen.getByText('0.50%')).toBeInTheDocument()
    })

    it('renders total return card', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total return/i)).toBeInTheDocument()
      })

      expect(screen.getByText('$15,000.00')).toBeInTheDocument()
      expect(screen.getByText('15.00%')).toBeInTheDocument()
    })

    it('renders positions card with correct position counts', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/positions/i)).toBeInTheDocument()
      })

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText(/4 long, 1 short/i)).toBeInTheDocument()
    })

    it('applies green color to positive P&L values', async () => {
      renderComponent()

      await waitFor(() => {
        const dailyPnlElement = screen.getByText('$500.00')
        expect(dailyPnlElement.parentElement).toHaveClass('text-green-600')
      })
    })

    it('applies red color to negative P&L values', async () => {
      const negativeMetrics = { ...mockMetrics }
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                ...mockSummary,
                daily_pnl: -200.0,
                daily_return_pct: -0.2,
              }),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(negativeMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        const negativePnl = screen.getByText('-$200.00')
        expect(negativePnl.parentElement).toHaveClass('text-red-600')
      })
    })
  })

  describe('Period Tabs', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('renders all period tabs', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /daily/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /weekly/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /monthly/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /yearly/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /all time/i })).toBeInTheDocument()
      })
    })

    it('switches to different period tab and fetches new metrics', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /monthly/i })).toBeInTheDocument()
      })

      const dailyTab = screen.getByRole('tab', { name: /daily/i })
      fireEvent.click(dailyTab)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('period=daily'),
          expect.any(Object)
        )
      })
    })

    it('fetches metrics with correct period parameter', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /weekly/i })).toBeInTheDocument()
      })

      const weeklyTab = screen.getByRole('tab', { name: /weekly/i })
      fireEvent.click(weeklyTab)

      await waitFor(() => {
        const calls = (global.fetch as jest.Mock).mock.calls
        const metricsCall = calls.find((call) =>
          call[0].includes('/portfolio/performance?period=weekly')
        )
        expect(metricsCall).toBeDefined()
      })
    })

    it('maintains tab state when switching between tabs', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /monthly/i })).toBeInTheDocument()
      })

      const yearlyTab = screen.getByRole('tab', { name: /yearly/i })
      fireEvent.click(yearlyTab)

      await waitFor(() => {
        expect(yearlyTab).toHaveAttribute('data-state', 'active')
      })
    })
  })

  describe('Performance Metrics', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('displays returns card with total return percentage', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/returns/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/total return/i)).toBeInTheDocument()
      expect(screen.getByText('15.00%')).toBeInTheDocument()
    })

    it('displays annualized return when available', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/annualized return/i)).toBeInTheDocument()
      })

      expect(screen.getByText('18.00%')).toBeInTheDocument()
    })

    it('displays risk metrics card with sharpe ratio', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/risk metrics/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/sharpe ratio/i)).toBeInTheDocument()
      expect(screen.getByText('1.80')).toBeInTheDocument()
    })

    it('displays sortino ratio', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/sortino ratio/i)).toBeInTheDocument()
      })

      expect(screen.getByText('2.10')).toBeInTheDocument()
    })

    it('displays max drawdown with red color styling', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/max drawdown/i)).toBeInTheDocument()
      })

      const maxDrawdownValue = screen.getByText('-8.50%')
      expect(maxDrawdownValue.parentElement).toHaveClass('text-red-600')
    })

    it('displays trading stats card with win rate', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/trading stats/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/win rate/i)).toBeInTheDocument()
      expect(screen.getByText('62.00%')).toBeInTheDocument()
    })

    it('displays profit factor', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/profit factor/i)).toBeInTheDocument()
      })

      expect(screen.getByText('2.30')).toBeInTheDocument()
    })
  })

  describe('Currency Formatting', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('formats large currency values correctly', async () => {
      const largeValueSummary = {
        ...mockSummary,
        total_equity: 1000000.0,
        cash_balance: 500000.0,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(largeValueSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('$1,000,000.00')).toBeInTheDocument()
      })
    })

    it('formats small currency values correctly', async () => {
      const smallValueSummary = {
        ...mockSummary,
        daily_pnl: 10.5,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(smallValueSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('$10.50')).toBeInTheDocument()
      })
    })

    it('formats zero values correctly', async () => {
      const zeroValueSummary = {
        ...mockSummary,
        daily_pnl: 0.0,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(zeroValueSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('$0.00')).toBeInTheDocument()
      })
    })

    it('formats negative currency values with minus sign', async () => {
      const negativeValueSummary = {
        ...mockSummary,
        total_pnl: -5000.0,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(negativeValueSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('-$5,000.00')).toBeInTheDocument()
      })
    })

    it('uses USD currency symbol', async () => {
      renderComponent()

      await waitFor(() => {
        const currencyElements = screen.getAllByText(/\$/g)
        expect(currencyElements.length).toBeGreaterThan(0)
        currencyElements.forEach((el) => {
          expect(el.textContent).toMatch(/\$/)
        })
      })
    })
  })

  describe('Percentage Formatting', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('formats percentages with two decimal places', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('15.00%')).toBeInTheDocument()
      })

      const percentElements = screen.getAllByText(/%/)
      expect(percentElements.length).toBeGreaterThan(0)
    })

    it('formats small percentage values correctly', async () => {
      const smallPercentMetrics = {
        ...mockMetrics,
        total_return_pct: 0.5,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(smallPercentMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('0.50%')).toBeInTheDocument()
      })
    })

    it('formats negative percentages correctly', async () => {
      const negativePercentMetrics = {
        ...mockMetrics,
        max_drawdown_pct: -8.5,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(negativePercentMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('-8.50%')).toBeInTheDocument()
      })
    })

    it('formats large percentage values correctly', async () => {
      const largePercentMetrics = {
        ...mockMetrics,
        total_return_pct: 150.5,
      }

      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(largePercentMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('150.50%')).toBeInTheDocument()
      })
    })

    it('converts decimal form to percentage correctly', async () => {
      renderComponent()

      await waitFor(() => {
        // The annualized_return is 0.18 in mockMetrics, should display as 18.00%
        expect(screen.getByText('18.00%')).toBeInTheDocument()
      })
    })
  })

  describe('Empty Metrics Handling', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetricsWithNulls),
          })
        }
      })
    })

    it('does not display annualized return when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/daily p&l/i)).toBeInTheDocument()
      })

      const annualizedReturnElements = screen.queryAllByText(/annualized return/i)
      expect(annualizedReturnElements.length).toBe(0)
    })

    it('does not display sharpe ratio when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/risk metrics/i)).toBeInTheDocument()
      })

      const sharpeRatioElements = screen.queryAllByText(/sharpe ratio/i)
      expect(sharpeRatioElements.length).toBe(0)
    })

    it('does not display sortino ratio when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/risk metrics/i)).toBeInTheDocument()
      })

      const sortinoRatioElements = screen.queryAllByText(/sortino ratio/i)
      expect(sortinoRatioElements.length).toBe(0)
    })

    it('does not display max drawdown when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/risk metrics/i)).toBeInTheDocument()
      })

      const maxDrawdownElements = screen.queryAllByText(/max drawdown/i)
      expect(maxDrawdownElements.length).toBe(0)
    })

    it('does not display win rate when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/trading stats/i)).toBeInTheDocument()
      })

      const winRateElements = screen.queryAllByText(/win rate/i)
      expect(winRateElements.length).toBe(0)
    })

    it('does not display profit factor when null', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/trading stats/i)).toBeInTheDocument()
      })

      const profitFactorElements = screen.queryAllByText(/profit factor/i)
      expect(profitFactorElements.length).toBe(0)
    })

    it('renders metric cards even with all null optional values', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/returns/i)).toBeInTheDocument()
        expect(screen.getByText(/risk metrics/i)).toBeInTheDocument()
        expect(screen.getByText(/trading stats/i)).toBeInTheDocument()
      })

      // Summary cards should still be visible
      expect(screen.getByText(/total equity/i)).toBeInTheDocument()
    })
  })

  describe('Page Header', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('renders page title "Portfolio Analytics"', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /portfolio analytics/i }))
          .toBeInTheDocument()
      })
    })

    it('displays title with proper styling', async () => {
      renderComponent()

      await waitFor(() => {
        const title = screen.getByRole('heading', { name: /portfolio analytics/i })
        expect(title).toHaveClass('text-3xl', 'font-bold')
      })
    })
  })

  describe('API Integration', () => {
    it('sends authorization header with token from localStorage', async () => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total equity/i)).toBeInTheDocument()
      })

      const calls = (global.fetch as jest.Mock).mock.calls
      calls.forEach((call) => {
        expect(call[1].headers).toEqual({
          Authorization: 'Bearer test-token',
        })
      })
    })

    it('calls summary endpoint', async () => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total equity/i)).toBeInTheDocument()
      })

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/portfolio/summary',
        expect.any(Object)
      )
    })

    it('calls performance endpoint with period parameter', async () => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total equity/i)).toBeInTheDocument()
      })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/portfolio/performance?period=monthly'),
        expect.any(Object)
      )
    })

    it('refetches metrics when period changes', async () => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /daily/i })).toBeInTheDocument()
      })

      const initialCallCount = (global.fetch as jest.Mock).mock.calls.length

      fireEvent.click(screen.getByRole('tab', { name: /daily/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('period=daily'),
          expect.any(Object)
        )
        expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(
          initialCallCount
        )
      })
    })
  })

  describe('Error Handling', () => {
    it('handles fetch errors gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

      ;(global.fetch as jest.Mock).mockRejectedValue(
        new Error('Network error')
      )

      renderComponent()

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalledWith(
          expect.stringContaining('Error fetching portfolio data'),
          expect.any(Error)
        )
      })

      consoleErrorSpy.mockRestore()
    })

    it('stops loading after error occurs', async () => {
      jest.spyOn(console, 'error').mockImplementation()

      ;(global.fetch as jest.Mock).mockRejectedValue(
        new Error('Network error')
      )

      renderComponent()

      await waitFor(() => {
        expect(
          screen.queryByText(/loading portfolio analytics/i)
        ).not.toBeInTheDocument()
      })
    })
  })

  describe('Responsive Layout', () => {
    beforeEach(() => {
      ;(global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/portfolio/summary')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockSummary),
          })
        }
        if (url.includes('/portfolio/performance')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockMetrics),
          })
        }
      })
    })

    it('renders grid layout for summary cards', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/total equity/i)).toBeInTheDocument()
      })

      const gridContainer = screen
        .getByText(/total equity/i)
        .closest('.grid')
      expect(gridContainer).toHaveClass('grid', 'gap-4')
    })

    it('renders metrics cards in grid layout', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/returns/i)).toBeInTheDocument()
      })

      const metricsGrid = screen
        .getByText(/returns/i)
        .closest('.grid')
      expect(metricsGrid).toHaveClass('grid', 'gap-4')
    })
  })
})
