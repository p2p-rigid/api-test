import React from 'react';
import { render, screen } from '@testing-library/react';
import MessageList from '../MessageList';
import { ChatMessage } from '@/lib/api';

describe('MessageList', () => {
  it('shows empty state when no messages', () => {
    render(<MessageList messages={[]} />);
    
    expect(screen.getByText('Start a conversation about users')).toBeInTheDocument();
    expect(screen.getByText(/e.g., "list all users"/)).toBeInTheDocument();
  });

  it('renders messages when provided', () => {
    const messages: ChatMessage[] = [
      {
        id: 'user_1',
        role: 'user',
        content: 'List users',
        timestamp: 1700000000000,
      },
      {
        id: 'assistant_1',
        role: 'assistant',
        content: 'Found 10 user(s)',
        timestamp: 1700000001000,
      },
    ];
    
    render(<MessageList messages={messages} />);
    
    expect(screen.getByText('List users')).toBeInTheDocument();
    expect(screen.getByText('Found 10 user(s)')).toBeInTheDocument();
  });

  it('does not show empty state when messages exist', () => {
    const messages: ChatMessage[] = [
      {
        id: 'user_1',
        role: 'user',
        content: 'Hello',
        timestamp: 1700000000000,
      },
    ];
    
    render(<MessageList messages={messages} />);
    
    expect(screen.queryByText('Start a conversation about users')).not.toBeInTheDocument();
  });
});
