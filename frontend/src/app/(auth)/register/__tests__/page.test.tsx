// frontend/src/app/(auth)/register/__tests__/page.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import RegisterPage from '../page'

// Mock the useRouter hook
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

describe('RegisterPage', () => {
  it('allows a user to register', async () => {
    render(<RegisterPage />)

    const nameInput = screen.getByLabelText(/name/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const registerButton = screen.getByRole('button', { name: /create account/i })

    // Provide valid input to the name, email, and password fields
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })

    // Now the button should be enabled
    expect(registerButton).toBeEnabled()

    fireEvent.click(registerButton)

    // Add assertions here to check for successful registration,
    // such as the user being redirected to the login page.
  })
})
