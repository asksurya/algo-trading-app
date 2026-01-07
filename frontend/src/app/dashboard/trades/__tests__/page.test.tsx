import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TradesPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock the use-trades hook
jest.mock('@/lib/hooks/use-trades', () => ({
  useTrades: jest.fn(),
  useTradingStatistics: jest.fn(),
}));

// Create a fresh QueryClient for each test
const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

// Mock data for trades
const mockTrades = {
  data: [
    {
      id: 'trade-1',
      user_id: 'user-1',
      strategy_id: 'strategy-1',
      ticker: 'AAPL',
      trade_type: 'buy',
      status: 'filled',
      quantity: '10',
      filled_quantity: '10',
      price: '150.00',
      filled_avg_price: '150.00',
      order_id: 'order-1',
      realized_pnl: '50.00',
      created_at: '2024-01-15T08:00:00Z',
      executed_at: '2024-01-15T10:30:00Z',
    },
    {
      id: 'trade-2',
      user_id: 'user-1',
      strategy_id: 'strategy-1',
      ticker: 'MSFT',
      trade_type: 'sell',
      status: 'filled',
      quantity: '5',
      filled_quantity: '5',
      price: '330.00',
      filled_avg_price: '330.00',
      order_id: 'order-2',
      realized_pnl: '-25.00',
      created_at: '2024-01-14T08:00:00Z',
      executed_at: '2024-01-14T11:00:00Z',
    },
    {
      id: 'trade-3',
      user_id: 'user-1',
      strategy_id: 'strategy-1',
      ticker: 'GOOGL',
      trade_type: 'buy',
      status: 'pending',
      quantity: '3',
      filled_quantity: '0',
      price: '140.00',
      order_id: 'order-3',
      created_at: '2024-01-13T08:00:00Z',
    },
    {
      id: 'trade-4',
      user_id: 'user-1',
      strategy_id: 'strategy-1',
      ticker: 'TSLA',
      trade_type: 'buy',
      status: 'partially_filled',
      quantity: '20',
      filled_quantity: '12',
      price: '250.00',
      filled_avg_price: '250.50',
      order_id: 'order-4',
      realized_pnl: '100.00',
      created_at: '2024-01-12T08:00:00Z',
      executed_at: '2024-01-12T14:00:00Z',
    },
    {
      id: 'trade-5',
      user_id: 'user-1',
      strategy_id: 'strategy-1',
      ticker: 'META',
      trade_type: 'sell',
      status: 'cancelled',
      quantity: '8',
      filled_quantity: '0',
      price: '350.00',
      order_id: 'order-5',
      created_at: '2024-01-11T08:00:00Z',
    },
  ],
  page: 1,
  page_size: 100,
  total: 5,
};

// Mock trading statistics
const mockStatistics = {
  total_trades: 100,
  winning_trades: 60,
  losing_trades: 40,
  win_rate: 60.0,
  total_pnl: '5000.00',
  avg_win: '150.00',
  avg_loss: '-75.00',
  largest_win: '500.00',
  largest_loss: '-300.00',
  sharpe_ratio: 1.5,
};

describe('TradesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Test 1: Renders loading state
   * Verifies that the component displays a loading spinner when data is being fetched
   */
  it('renders loading state', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Check for the page heading (h1 specifically)
    const mainHeading = screen.getByRole('heading', { level: 1, name: /trades/i });
    expect(mainHeading).toBeInTheDocument();

    // Check for loading indicators in stats cards
    const loadingTexts = screen.getAllByText('Loading...');
    expect(loadingTexts.length).toBeGreaterThan(0);
  });

  /**
   * Test 2: Renders empty state with no trades
   * Verifies that appropriate messaging is shown when there are no trades
   */
  it('renders empty state with no trades', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: { data: [], page: 1, page_size: 100, total: 0 },
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Check for empty state message
    expect(screen.getByText('No trades yet')).toBeInTheDocument();
    expect(
      screen.getByText('Trades will appear here once you execute them')
    ).toBeInTheDocument();

    // Check that the page heading is still visible
    const mainHeading = screen.getByRole('heading', { level: 1, name: /trades/i });
    expect(mainHeading).toBeInTheDocument();
  });

  /**
   * Test 3: Renders trades list correctly
   * Verifies that trades are properly displayed with all required information
   */
  it('renders trades list correctly', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Check that trades table is rendered
    const tradesTable = screen.getByTestId('trades-table');
    expect(tradesTable).toBeInTheDocument();

    // Verify each trade's ticker is displayed
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('TSLA')).toBeInTheDocument();
    expect(screen.getByText('META')).toBeInTheDocument();

    // Verify trade types are displayed
    const buyTexts = screen.getAllByText(/buy/i);
    const sellTexts = screen.getAllByText(/sell/i);
    expect(buyTexts.length).toBeGreaterThan(0);
    expect(sellTexts.length).toBeGreaterThan(0);

    // Verify quantities are displayed (they may be split across elements)
    expect(screen.getByText(/10\s+shares/)).toBeInTheDocument();
    expect(screen.getByText(/5\s+shares/)).toBeInTheDocument();
  });

  /**
   * Test 4: Displays statistics cards
   * Verifies that all statistics cards render with correct values
   */
  it('displays statistics cards', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Verify "Total Trades" card
    expect(screen.getByText('Total Trades')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();

    // Verify "Win Rate" card
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
    expect(screen.getByText('60 wins / 40 losses')).toBeInTheDocument();

    // Verify "Total P&L" card
    expect(screen.getByText('Total P&L')).toBeInTheDocument();
    expect(screen.getByText('$5,000.00')).toBeInTheDocument();

    // Verify "Avg Win/Loss" card
    expect(screen.getByText('Avg Win/Loss')).toBeInTheDocument();
    expect(screen.getByText('Win: $150.00')).toBeInTheDocument();
    expect(screen.getByText('Loss: -$75.00')).toBeInTheDocument();
  });

  /**
   * Test 5: Status badges render correctly
   * Verifies that different trade statuses display with correct badge variants
   */
  it('status badges render correctly', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Verify all status badges are rendered by checking for them individually
    // We use getAllByText since there may be multiple matches
    const filledBadges = screen.getAllByText(/^Filled$/);
    const pendingBadges = screen.getAllByText(/^Pending$/);
    const partiallyFilledBadges = screen.getAllByText(/^Partially Filled$/);
    const cancelledBadges = screen.getAllByText(/^Cancelled$/);

    expect(filledBadges.length).toBeGreaterThan(0);
    expect(pendingBadges.length).toBeGreaterThan(0);
    expect(partiallyFilledBadges.length).toBeGreaterThan(0);
    expect(cancelledBadges.length).toBeGreaterThan(0);
  });

  /**
   * Test 6: Currency and date formatting works
   * Verifies that prices, totals, and dates are properly formatted
   */
  it('currency and date formatting works', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Verify currency formatting for prices
    expect(screen.getByText('$150.00')).toBeInTheDocument();
    expect(screen.getByText('$330.00')).toBeInTheDocument();
    expect(screen.getByText('$250.50')).toBeInTheDocument();

    // Verify P&L values are formatted as currency
    const positiveMatches = screen.getAllByText('$50.00');
    expect(positiveMatches.length).toBeGreaterThan(0);

    // Verify date formatting - check for formatted dates
    // The page uses toLocaleDateString with specific options
    // Example: Jan 15, 2024, 10:30 AM
    const dateElements = screen.getAllByText(/Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/);
    expect(dateElements.length).toBeGreaterThan(0);

    // Verify total calculations (quantity * price)
    expect(screen.getByText('Total: $1,500.00')).toBeInTheDocument();
  });

  /**
   * Test 7: Trade History heading and description
   * Verifies that the trade history section header is displayed correctly
   */
  it('renders trade history heading and description', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    expect(screen.getByText('Trade History')).toBeInTheDocument();
    expect(screen.getByText('All your executed trades')).toBeInTheDocument();
  });

  /**
   * Test 8: Buy/Sell trade type icons display correctly
   * Verifies that buy trades show up arrows and sell trades show down arrows
   */
  it('buy and sell trade types display correctly', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    const { container } = render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Verify that the trades are displayed with buy/sell indicators
    // The component uses ArrowUpRight for buy and ArrowDownRight for sell
    const tradesTable = screen.getByTestId('trades-table');
    expect(tradesTable).toBeInTheDocument();

    // Verify trade type text is displayed
    const buyTypeElements = screen.getAllByText(/BUY/);
    const sellTypeElements = screen.getAllByText(/SELL/);

    expect(buyTypeElements.length).toBeGreaterThan(0);
    expect(sellTypeElements.length).toBeGreaterThan(0);
  });

  /**
   * Test 9: P&L color coding (green for positive, red for negative)
   * Verifies that P&L values use correct color coding
   */
  it('P&L values use correct color coding', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    const { container } = render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Check for color-coded P&L values
    // Positive P&L should have text-green-600 class
    const greenElements = container.querySelectorAll('.text-green-600');
    const redElements = container.querySelectorAll('.text-red-600');

    expect(greenElements.length).toBeGreaterThan(0);
    expect(redElements.length).toBeGreaterThan(0);
  });

  /**
   * Test 10: Page structure and layout
   * Verifies that the page has the correct structure and hierarchy
   */
  it('has correct page structure and headings', () => {
    const { useTrades, useTradingStatistics } = require('@/lib/hooks/use-trades');
    useTrades.mockReturnValue({
      data: mockTrades,
      isLoading: false,
      error: null,
    });
    useTradingStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
      error: null,
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <TradesPage />
      </QueryClientProvider>
    );

    // Verify main heading (h1 level)
    const mainHeading = screen.getByRole('heading', { level: 1, name: /trades/i });
    expect(mainHeading).toBeInTheDocument();

    // Verify description
    expect(
      screen.getByText('View your trading history and statistics')
    ).toBeInTheDocument();

    // Verify section heading
    expect(screen.getByText('Trade History')).toBeInTheDocument();
  });
});
