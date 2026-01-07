"use client";

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import StrategiesPage from "../page";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

// Mock useStrategies hook
jest.mock("@/lib/hooks/use-strategies", () => ({
  useStrategies: jest.fn(),
  useDeleteStrategy: jest.fn(),
  useUpdateStrategy: jest.fn(),
}));

// Mock useCurrentPositions hook
jest.mock("@/lib/hooks/use-trades", () => ({
  useCurrentPositions: jest.fn(),
}));

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  Plus: () => <span data-testid="plus-icon">+</span>,
  TrendingUp: () => <span data-testid="trending-up-icon">📈</span>,
  TrendingDown: () => <span data-testid="trending-down-icon">📉</span>,
  Loader2: () => <span data-testid="loader-icon">⏳</span>,
  Trash2: () => <span data-testid="trash-icon">🗑️</span>,
}));

// Mock shadcn/ui components
jest.mock("@/components/ui/button", () => ({
  Button: ({
    children,
    "data-testid": testId,
    onClick,
    disabled,
    variant,
    size,
    className,
  }: any) => (
    <button
      data-testid={testId}
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/card", () => ({
  Card: ({ children, "data-testid": testId }: any) => (
    <div data-testid={testId} className="card">
      {children}
    </div>
  ),
  CardHeader: ({ children }: any) => <div className="card-header">{children}</div>,
  CardTitle: ({ children, className }: any) => (
    <h2 className={className}>{children}</h2>
  ),
  CardDescription: ({ children }: any) => <p>{children}</p>,
  CardContent: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({
    children,
    variant,
    className,
    onClick,
  }: any) => (
    <span
      data-testid="badge"
      className={className}
      onClick={onClick}
      data-variant={variant}
    >
      {children}
    </span>
  ),
}));

// Mock data
const mockStrategies = [
  {
    id: "strategy-1",
    name: "SMA Crossover",
    strategy_type: "sma_crossover",
    description: "Simple Moving Average Crossover Strategy",
    is_active: true,
    is_backtested: true,
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "strategy-2",
    name: "RSI Momentum",
    strategy_type: "rsi",
    description: "RSI-based momentum strategy",
    is_active: false,
    is_backtested: false,
    created_at: "2024-01-15T00:00:00Z",
  },
  {
    id: "strategy-3",
    name: "MACD Trading",
    strategy_type: "macd",
    description: null,
    is_active: true,
    is_backtested: true,
    created_at: "2024-02-01T00:00:00Z",
  },
];

const mockPositions = [
  {
    id: "pos-1",
    strategy_id: "strategy-1",
    symbol: "AAPL",
    quantity: "10",
    current_price: "150.00",
    unrealized_pnl: "500.00",
    realized_pnl: "0.00",
  },
  {
    id: "pos-2",
    strategy_id: "strategy-1",
    symbol: "GOOGL",
    quantity: "5",
    current_price: "140.00",
    unrealized_pnl: "-100.00",
    realized_pnl: "200.00",
  },
  {
    id: "pos-3",
    strategy_id: "strategy-2",
    symbol: "MSFT",
    quantity: "20",
    current_price: "380.00",
    unrealized_pnl: "1000.00",
    realized_pnl: "-50.00",
  },
];

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const client = createQueryClient();
  return render(
    <QueryClientProvider client={client}>{component}</QueryClientProvider>
  );
};

describe("StrategiesPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set default mock returns for mutation hooks
    const { useDeleteStrategy, useUpdateStrategy } = require("@/lib/hooks/use-strategies");
    useDeleteStrategy.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });
    useUpdateStrategy.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    });
  });

  // Test 1: Renders loading state
  describe("Loading State", () => {
    it("renders loading state when strategies are being fetched", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: undefined,
        isLoading: true,
      });
      useCurrentPositions.mockReturnValue({
        data: [],
      });

      renderWithQueryClient(<StrategiesPage />);

      expect(screen.getByTestId("loader-icon")).toBeInTheDocument();
      expect(screen.getByText("Strategies")).toBeInTheDocument();
    });
  });

  // Test 2: Renders empty state with no strategies
  describe("Empty State", () => {
    it("renders empty state when no strategies exist", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: [],
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: [],
      });

      renderWithQueryClient(<StrategiesPage />);

      expect(screen.getByText("No strategies yet")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Create Your First Strategy/i })
      ).toBeInTheDocument();
    });
  });

  // Test 3: Renders strategy cards correctly
  describe("Strategy Cards", () => {
    it("renders strategy cards with correct information", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Check that all strategy names are rendered
      expect(screen.getByText("SMA Crossover")).toBeInTheDocument();
      expect(screen.getByText("RSI Momentum")).toBeInTheDocument();
      expect(screen.getByText("MACD Trading")).toBeInTheDocument();

      // Check that descriptions are rendered
      expect(
        screen.getByText("Simple Moving Average Crossover Strategy")
      ).toBeInTheDocument();
      expect(screen.getByText("RSI-based momentum strategy")).toBeInTheDocument();
    });

    it("renders strategy type when description is null", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });

      renderWithQueryClient(<StrategiesPage />);

      // MACD Trading has null description, should show strategy_type
      expect(screen.getByText("macd")).toBeInTheDocument();
    });

    it("renders all strategy cards in grid layout", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });

      renderWithQueryClient(<StrategiesPage />);

      const strategiesTable = screen.getByTestId("strategies-table");
      expect(strategiesTable).toBeInTheDocument();
      expect(strategiesTable.querySelectorAll(".card")).toHaveLength(3);
    });
  });

  // Test 4: Create button present with testid
  describe("Create Button", () => {
    it("renders create strategy button with correct testid", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });

      renderWithQueryClient(<StrategiesPage />);

      const createButton = screen.getByTestId("create-strategy-button");
      expect(createButton).toBeInTheDocument();
      expect(createButton).toHaveTextContent("New Strategy");
    });

    it("create button has correct href link", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: [],
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: [],
      });

      renderWithQueryClient(<StrategiesPage />);

      const createButton = screen.getByRole("button", {
        name: /Create Your First Strategy/i,
      });
      const parentLink = createButton.closest("a");
      expect(parentLink).toHaveAttribute("href", "/dashboard/strategies/new");
    });
  });

  // Test 5: Active/inactive toggle works
  describe("Active/Inactive Toggle", () => {
    it("renders status badge for each strategy", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const badges = screen.getAllByTestId("badge");
      expect(badges.length).toBeGreaterThan(0);
      expect(badges.some((badge) => badge.textContent === "Active")).toBe(true);
      expect(badges.some((badge) => badge.textContent === "Inactive")).toBe(true);
    });

    it("calls updateStrategy when status badge is clicked", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      const mockMutate = jest.fn();
      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const badges = screen.getAllByTestId("badge");
      // Click the first Active badge
      const activeBadge = badges.find((badge) => badge.textContent === "Active");
      if (activeBadge) {
        fireEvent.click(activeBadge);
        expect(mockMutate).toHaveBeenCalledWith({
          id: "strategy-1",
          data: { is_active: false },
        });
      }
    });

    it("displays correct badge variant for active strategies", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const badges = screen.getAllByTestId("badge");
      const activeBadges = badges.filter(
        (badge) => badge.getAttribute("data-variant") === "default"
      );
      expect(activeBadges.length).toBeGreaterThan(0);
    });
  });

  // Test 6: Delete confirmation shows
  describe("Delete Functionality", () => {
    it("shows confirmation dialog when delete button is clicked", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useDeleteStrategy } = require("@/lib/hooks/use-strategies");

      const mockConfirm = jest.spyOn(window, "confirm");
      mockConfirm.mockReturnValue(false);

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useDeleteStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const trashButtons = screen.getAllByTestId("trash-icon");
      fireEvent.click(trashButtons[0].closest("button")!);

      expect(mockConfirm).toHaveBeenCalledWith(
        'Are you sure you want to delete "SMA Crossover"?'
      );

      mockConfirm.mockRestore();
    });

    it("calls deleteStrategy.mutate when user confirms deletion", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useDeleteStrategy } = require("@/lib/hooks/use-strategies");

      const mockMutate = jest.fn();
      const mockConfirm = jest.spyOn(window, "confirm");
      mockConfirm.mockReturnValue(true);

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useDeleteStrategy.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const trashButtons = screen.getAllByTestId("trash-icon");
      fireEvent.click(trashButtons[0].closest("button")!);

      expect(mockMutate).toHaveBeenCalledWith("strategy-1");

      mockConfirm.mockRestore();
    });

    it("does not call deleteStrategy.mutate when user cancels confirmation", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useDeleteStrategy } = require("@/lib/hooks/use-strategies");

      const mockMutate = jest.fn();
      const mockConfirm = jest.spyOn(window, "confirm");
      mockConfirm.mockReturnValue(false);

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useDeleteStrategy.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const trashButtons = screen.getAllByTestId("trash-icon");
      fireEvent.click(trashButtons[0].closest("button")!);

      expect(mockMutate).not.toHaveBeenCalled();

      mockConfirm.mockRestore();
    });

    it("disables delete button while deletion is pending", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useDeleteStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useDeleteStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: true,
      });

      renderWithQueryClient(<StrategiesPage />);

      const deleteButtons = screen.getAllByRole("button").filter((btn) => {
        return btn.querySelector("[data-testid='trash-icon']");
      });

      deleteButtons.forEach((btn) => {
        expect(btn).toBeDisabled();
      });
    });
  });

  // Test 7: P&L calculations display
  describe("P&L Calculations", () => {
    it("displays P&L for strategies with positions", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 1 has positions, should show P&L
      // pos-1: unrealized 500 + realized 0 = 500
      // pos-2: unrealized -100 + realized 200 = 100
      // Total P&L = 600
      expect(screen.getByText(/\$600\.00/)).toBeInTheDocument();
    });

    it("displays P&L as positive with green styling when profitable", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 1 is profitable (P&L = 600)
      const pnlText = screen.getByText(/\$600\.00 \(\+/);
      expect(pnlText).toHaveClass("text-green-600");
    });

    it("displays P&L as negative with red styling when loss", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      const negativePositions = [
        {
          id: "pos-1",
          strategy_id: "strategy-2",
          symbol: "AAPL",
          quantity: "10",
          current_price: "100.00",
          unrealized_pnl: "-500.00",
          realized_pnl: "-100.00",
        },
      ];

      useStrategies.mockReturnValue({
        data: [mockStrategies[1]],
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: negativePositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 2 has negative P&L
      const pnlText = screen.getByText(/\-\$600\.00 \(\-/);
      expect(pnlText).toHaveClass("text-red-600");
    });

    it("displays position count correctly", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 1 has 2 positions
      const positionCounts = screen.getAllByText((_, element) => {
        return element?.textContent?.match(/^(2|1)$/) !== null;
      });
      expect(positionCounts.length).toBeGreaterThan(0);
    });

    it("displays position value in currency format", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Check for currency formatting
      const currencyElements = screen.getAllByText(/\$[\d,]+\.\d{2}/);
      expect(currencyElements.length).toBeGreaterThan(0);
    });

    it("displays P&L percentage formatting correctly", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Check for percentage formatting with + or - prefix
      const percentageElements = screen.getAllByText(/([+-]\d+\.\d{2}%)/);
      expect(percentageElements.length).toBeGreaterThan(0);
    });
  });

  // Additional Test: Trending indicators
  describe("Trending Indicators", () => {
    it("displays TrendingUp icon for profitable strategies", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 1 has positive P&L, should show trending up
      const trendingUpIcons = screen.getAllByTestId("trending-up-icon");
      expect(trendingUpIcons.length).toBeGreaterThan(0);
    });

    it("displays TrendingDown icon for loss-making strategies", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      const negativePositions = [
        {
          id: "pos-1",
          strategy_id: "strategy-2",
          symbol: "AAPL",
          quantity: "10",
          current_price: "100.00",
          unrealized_pnl: "-500.00",
          realized_pnl: "-100.00",
        },
      ];

      useStrategies.mockReturnValue({
        data: [mockStrategies[1]],
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: negativePositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Strategy 2 has negative P&L, should show trending down
      expect(screen.getByTestId("trending-down-icon")).toBeInTheDocument();
    });

    it("does not display trending indicator when P&L is zero", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      const zeroPositions = [
        {
          id: "pos-1",
          strategy_id: "strategy-3",
          symbol: "AAPL",
          quantity: "10",
          current_price: "100.00",
          unrealized_pnl: "0.00",
          realized_pnl: "0.00",
        },
      ];

      useStrategies.mockReturnValue({
        data: [mockStrategies[2]],
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: zeroPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // When P&L is 0, no trending indicator should be shown
      expect(screen.queryByTestId("trending-up-icon")).not.toBeInTheDocument();
      expect(screen.queryByTestId("trending-down-icon")).not.toBeInTheDocument();
    });
  });

  // Additional Test: Backtested badge
  describe("Backtested Badge", () => {
    it("displays backtested badge for backtested strategies", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const badges = screen.getAllByTestId("badge");
      const backtestBadges = badges.filter(
        (badge) => badge.textContent === "Yes"
      );
      // Strategy 1 and 3 are backtested
      expect(backtestBadges.length).toBeGreaterThanOrEqual(2);
    });

    it("does not display backtested badge for non-backtested strategies", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: [mockStrategies[1]], // RSI Momentum, is_backtested: false
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      // Only status badge should be present, not backtested badge
      const badges = screen.getAllByTestId("badge");
      const backtestBadges = badges.filter(
        (badge) => badge.textContent === "Yes"
      );
      expect(backtestBadges.length).toBe(0);
    });
  });

  // Additional Test: View Details Link
  describe("View Details Link", () => {
    it("renders View Details button for each strategy", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const viewButtons = screen.getAllByRole("button", {
        name: /View Details/i,
      });
      expect(viewButtons).toHaveLength(mockStrategies.length);
    });

    it("View Details button links to correct strategy page", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");
      const { useUpdateStrategy } = require("@/lib/hooks/use-strategies");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });
      useUpdateStrategy.mockReturnValue({
        mutate: jest.fn(),
        isPending: false,
      });

      renderWithQueryClient(<StrategiesPage />);

      const viewButtons = screen.getAllByRole("button", {
        name: /View Details/i,
      });
      const links = viewButtons.map((btn) => btn.closest("a"));

      expect(links[0]).toHaveAttribute("href", "/dashboard/strategies/strategy-1");
      expect(links[1]).toHaveAttribute("href", "/dashboard/strategies/strategy-2");
      expect(links[2]).toHaveAttribute("href", "/dashboard/strategies/strategy-3");
    });
  });

  // Additional Test: Page header
  describe("Page Header", () => {
    it("renders page title and description", () => {
      const { useStrategies } = require("@/lib/hooks/use-strategies");
      const { useCurrentPositions } = require("@/lib/hooks/use-trades");

      useStrategies.mockReturnValue({
        data: mockStrategies,
        isLoading: false,
      });
      useCurrentPositions.mockReturnValue({
        data: mockPositions,
      });

      renderWithQueryClient(<StrategiesPage />);

      expect(screen.getByText("Strategies")).toBeInTheDocument();
      expect(
        screen.getByText("Manage your trading strategies")
      ).toBeInTheDocument();
    });
  });
});
