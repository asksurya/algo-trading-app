// frontend/src/app/(auth)/login/__tests__/page.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import LoginPage from '../page'

// Mock the useRouter hook
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('LoginPage', () => {
  it('allows a user to log in', async () => {
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const loginButton = screen.getByRole('button', { name: /login/i })

    // Provide valid input to the email and password fields
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })

    // Now the button should be enabled
    expect(loginButton).toBeEnabled()

    fireEvent.click(loginButton)

    // Add assertions here to check for successful login,
    // such as the user being redirected to the dashboard.
  })
})
