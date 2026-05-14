import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '@/lib/api';
import MessageBubble from './MessageBubble';

interface MessageWithResponse extends ChatMessage {
  fullResponse?: {
    summary: string;
    intent: string;
    data: any[];
    filters: Record<string, any>;
    count: number;
    error: string | null;
    session_id: string | null;
  };
}

interface MessageListProps {
  messages: MessageWithResponse[];
}

const MAX_WIDTH = '768px';

export default function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
      <div style={{ maxWidth: MAX_WIDTH, margin: '0 auto' }}>
        {messages.length === 0 && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '8px' }}>💬</div>
              <div>Start a conversation about users</div>
              <div style={{ fontSize: '14px', marginTop: '4px' }}>e.g., "list all users" or "find user with email test@example.com"</div>
            </div>
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} fullResponse={message.fullResponse} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
