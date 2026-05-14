'use client';

import React, { useState } from 'react';
import { ChatMessage, sendMessage, clearSession, QueryResponse } from '@/lib/api';
import MessageList from './MessageList';
import InputArea from './InputArea';

const MAX_WIDTH = '768px';

interface MessageWithResponse extends ChatMessage {
  fullResponse?: QueryResponse;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<MessageWithResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (content: string) => {
    const userMessage: MessageWithResponse = {
      id: 'user_' + Date.now(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const { response, messages: assistantMessages } = await sendMessage(content);
      
      const assistantMessage: MessageWithResponse = {
        id: 'assistant_' + Date.now(),
        role: 'assistant',
        content: response.summary,
        data: response.data,
        intent: response.intent,
        timestamp: Date.now(),
        fullResponse: response,
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    clearSession();
    setMessages([]);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#fff' }}>
      {/* Header */}
      <header style={{ backgroundColor: '#fff', borderBottom: '1px solid #e5e7eb', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ maxWidth: MAX_WIDTH, margin: '0 auto', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '32px', height: '32px', backgroundColor: '#2563eb', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: 'white', fontWeight: 600, fontSize: '14px' }}>U</span>
            </div>
            <h1 style={{ fontSize: '18px', fontWeight: 600, color: '#111827', margin: 0 }}>User Query Chat</h1>
          </div>
          <button
            onClick={handleClear}
            style={{ fontSize: '14px', color: '#6b7280', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 12px', borderRadius: '4px' }}
            onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#f3f4f6')}
            onMouseOut={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
          >
            New Chat
          </button>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div style={{ backgroundColor: '#fef2f2', borderBottom: '1px solid #fecaca', padding: '8px 16px', color: '#dc2626', fontSize: '14px' }}>
          <div style={{ maxWidth: MAX_WIDTH, margin: '0 auto' }}>{error}</div>
        </div>
      )}

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <InputArea onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
