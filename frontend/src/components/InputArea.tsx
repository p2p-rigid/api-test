import React, { useState, KeyboardEvent } from 'react';

interface InputAreaProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const MAX_WIDTH = '768px';

export default function InputArea({ onSend, disabled }: InputAreaProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ borderTop: '1px solid #e5e7eb', padding: '16px', backgroundColor: '#fff' }}>
      <div style={{ maxWidth: MAX_WIDTH, margin: '0 auto', display: 'flex', gap: '8px' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about users..."
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            borderRadius: '8px',
            border: '1px solid #d1d5db',
            padding: '8px 16px',
            fontSize: '14px',
            outline: 'none',
            minHeight: '44px',
            maxHeight: '120px',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          style={{
            padding: '8px 24px',
            backgroundColor: disabled || !input.trim() ? '#9ca3af' : '#2563eb',
            color: 'white',
            borderRadius: '8px',
            border: 'none',
            cursor: disabled || !input.trim() ? 'not-allowed' : 'pointer',
            fontWeight: 500,
            fontSize: '14px',
            transition: 'background-color 0.15s',
          }}
        >
          {disabled ? '...' : 'Send'}
        </button>
      </div>
      <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '12px', color: '#9ca3af' }}>
        Press Enter to send, Shift+Enter for new line
      </div>
    </div>
  );
}
