import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { AuthPage } from './AuthPage';
import { useAuth } from '../../hooks/useAuth';

vi.mock('../../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

describe('AuthPage', () => {
  it('submits login credentials', async () => {
    const loginMock = vi.fn().mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer',
      user: {
        id: 'user-1',
        email: 'jane@example.com',
        full_name: 'Jane Doe',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    });

    mockedUseAuth.mockReturnValue({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      login: loginMock,
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });

    render(
      <MemoryRouter>
        <AuthPage />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText(/email/i), 'jane@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'secret123');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({ email: 'jane@example.com', password: 'secret123' });
    });
  });
});
