// frontend/src/app/__tests__/page.test.tsx
import { render, screen } from '@testing-library/react'
import HomePage from '../page'

describe('HomePage', () => {
  it('renders the main heading', () => {
    render(<HomePage />)
    const heading = screen.getByRole('heading', {
      name: /Advanced Algorithmic Trading Platform/i,
    })
    expect(heading).toBeInTheDocument()
  })
})
