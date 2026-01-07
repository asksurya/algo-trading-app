import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SettingsPage from '../page';
import { useAuthStore } from '@/lib/stores/auth-store';

// Mock the auth store
jest.mock('@/lib/stores/auth-store', () => ({
  useAuthStore: jest.fn(),
}));

// Mock the toast hook
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('SettingsPage', () => {
  beforeEach(() => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockUser,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders settings page header', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText(/manage your account settings/i)).toBeInTheDocument();
  });

  it('displays user information', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('user')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Active')).toBeInTheDocument();
  });

  it('shows account information section', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Account Information')).toBeInTheDocument();
    expect(screen.getByText('Your account details')).toBeInTheDocument();
  });

  it('shows trading configuration section', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Trading Configuration')).toBeInTheDocument();
    expect(screen.getByLabelText(/alpaca api key/i)).toBeInTheDocument();
  });

  it('shows risk management section', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Risk Management')).toBeInTheDocument();
    expect(screen.getByLabelText(/max position size/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/stop loss/i)).toBeInTheDocument();
  });

  it('shows notifications section', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Trade Alerts')).toBeInTheDocument();
    expect(screen.getByText('Strategy Alerts')).toBeInTheDocument();
    expect(screen.getByText('Email Notifications')).toBeInTheDocument();
  });

  it('shows about section with feature lists', () => {
    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByText('About This Application')).toBeInTheDocument();
    expect(screen.getByText(/implemented features/i)).toBeInTheDocument();
    // Use a more specific text since "Coming Soon" appears in multiple places
    expect(screen.getByText('🚧 Coming Soon:')).toBeInTheDocument();
  });

  it('shows inactive status when user is not active', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: { ...mockUser, is_active: false },
    });

    render(<SettingsPage />, { wrapper: createWrapper() });

    expect(screen.getByDisplayValue('Inactive')).toBeInTheDocument();
  });

  it('handles null user gracefully', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: null,
    });

    render(<SettingsPage />, { wrapper: createWrapper() });

    // Should render without crashing
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
