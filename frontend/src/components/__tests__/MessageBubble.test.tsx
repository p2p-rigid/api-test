import React from 'react';
import { render, screen } from '@testing-library/react';
import MessageBubble from '../MessageBubble';
import { ChatMessage, QueryResponse } from '@/lib/api';

describe('MessageBubble', () => {
  const userMessage: ChatMessage = {
    id: 'user_1',
    role: 'user',
    content: 'Hello, list all users',
    timestamp: 1700000000000,
  };

  const assistantMessage: ChatMessage = {
    id: 'assistant_1',
    role: 'assistant',
    content: 'Found 13 user(s).',
    data: [
      {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        is_active: true,
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00',
      },
    ],
    intent: 'list_users',
    timestamp: 1700000001000,
  };

  const fullResponse: QueryResponse = {
    summary: 'Found 13 user(s).',
    intent: 'list_users',
    data: [
      {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        is_active: true,
        created_at: '2024-01-01T00:00:00',
        updated_at: '2024-01-01T00:00:00',
      },
    ],
    filters: {},
    count: 1,
    error: null,
    session_id: 'test-session',
  };

  it('renders user message on the right', () => {
    render(<MessageBubble message={userMessage} />);
    const bubble = screen.getByText('Hello, list all users');
    expect(bubble).toBeInTheDocument();
  });

  it('renders assistant message on the left', () => {
    render(<MessageBubble message={assistantMessage} />);
    const content = screen.getByText('Found 13 user(s).');
    expect(content).toBeInTheDocument();
  });

  it('displays user data when fullResponse is provided', () => {
    render(<MessageBubble message={assistantMessage} fullResponse={fullResponse} />);
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('shows user count when fullResponse is present', () => {
    render(<MessageBubble message={assistantMessage} fullResponse={fullResponse} />);
    expect(screen.getAllByText(/Found \d+ user\(s\)/).length).toBeGreaterThan(0);
  });

  it('displays intent badge when fullResponse is provided', () => {
    render(<MessageBubble message={assistantMessage} fullResponse={fullResponse} />);
    expect(screen.getByText('list_users')).toBeInTheDocument();
  });
});
