import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InputArea from '../InputArea';

describe('InputArea', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input field and send button', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    expect(screen.getByPlaceholderText('Ask about users...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('calls onSend when send button is clicked', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Ask about users...');
    fireEvent.change(input, { target: { value: 'list users' } });
    
    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalledWith('list users');
  });

  it('calls onSend when Enter is pressed', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Ask about users...');
    fireEvent.change(input, { target: { value: 'show active users' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockOnSend).toHaveBeenCalledWith('show active users');
  });

  it('does not send empty messages', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);
    
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('does not send when disabled', () => {
    render(<InputArea onSend={mockOnSend} disabled={true} />);
    
    const input = screen.getByPlaceholderText('Ask about users...');
    fireEvent.change(input, { target: { value: 'test' } });
    
    const sendButton = screen.getByText('...');
    expect(sendButton).toBeDisabled();
  });

  it('clears input after sending', () => {
    render(<InputArea onSend={mockOnSend} />);
    
    const input = screen.getByPlaceholderText('Ask about users...');
    fireEvent.change(input, { target: { value: 'list users' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(input).toHaveValue('');
  });
});
