import React from 'react';
import { ChatMessage, UserPublic, QueryResponse } from '@/lib/api';

interface MessageBubbleProps {
  message: ChatMessage;
  fullResponse?: QueryResponse;
}

export default function MessageBubble({ message, fullResponse }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: '16px' }}>
      <div
        style={{
          maxWidth: '90%',
          borderRadius: '8px',
          padding: '12px 16px',
          backgroundColor: isUser ? '#2563eb' : '#f9fafb',
          color: isUser ? 'white' : '#111827',
          border: isUser ? 'none' : '1px solid #e5e7eb',
        }}
      >
        {/* Summary text */}
        <div style={{ whiteSpace: 'pre-wrap', fontSize: '14px', marginBottom: fullResponse ? '12px' : '0' }}>
          {message.content}
        </div>
        
        {/* Full JSON response */}
        {fullResponse && !isUser && (
          <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px', color: '#374151' }}>
              Response Details
            </div>
            
            {/* Intent badge */}
            <div style={{ marginBottom: '12px' }}>
              <span style={{ 
                display: 'inline-block',
                padding: '2px 8px', 
                borderRadius: '4px', 
                fontSize: '11px',
                fontWeight: 500,
                backgroundColor: '#dbeafe',
                color: '#1e40af',
                textTransform: 'uppercase',
              }}>
                {fullResponse.intent}
              </span>
            </div>
            
            {/* JSON data */}
            <pre style={{ 
              margin: 0, 
              padding: '12px', 
              backgroundColor: '#1f2937', 
              borderRadius: '6px', 
              overflow: 'auto',
              fontSize: '11px',
              fontFamily: 'Monaco, Menlo, monospace',
              color: '#e5e7eb',
              maxHeight: '300px',
            }}>
{JSON.stringify(fullResponse, null, 2)}
            </pre>
            
            {/* User data table */}
            {fullResponse.data && fullResponse.data.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px', color: '#374151' }}>
                  Users ({fullResponse.data.length})
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: '#6b7280' }}>ID</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: '#6b7280' }}>Name</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: '#6b7280' }}>Email</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: '#6b7280' }}>Username</th>
                        <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: '#6b7280' }}>Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fullResponse.data.map((user: UserPublic) => (
                        <tr key={user.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                          <td style={{ padding: '6px 8px' }}>{user.id}</td>
                          <td style={{ padding: '6px 8px' }}>{user.first_name} {user.last_name}</td>
                          <td style={{ padding: '6px 8px' }}>{user.email}</td>
                          <td style={{ padding: '6px 8px' }}>@{user.username}</td>
                          <td style={{ padding: '6px 8px' }}>
                            <span style={{ 
                              padding: '2px 6px', 
                              borderRadius: '4px', 
                              fontSize: '10px',
                              backgroundColor: user.is_active ? '#d1fae5' : '#fee2e2',
                              color: user.is_active ? '#065f46' : '#991b1b',
                            }}>
                              {user.is_active ? 'Yes' : 'No'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Filters */}
            {fullResponse.filters && Object.keys(fullResponse.filters).length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px', color: '#374151' }}>
                  Filters
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {Object.entries(fullResponse.filters).map(([key, value]) => (
                    <span key={key} style={{ 
                      padding: '2px 8px', 
                      borderRadius: '4px', 
                      fontSize: '11px',
                      backgroundColor: '#f3f4f6',
                      color: '#4b5563',
                    }}>
                      {key}: {String(value)}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {/* Metadata */}
            <div style={{ marginTop: '12px', fontSize: '11px', color: '#9ca3af' }}>
              <div>Count: {fullResponse.count}</div>
              {fullResponse.session_id && <div>Session: {fullResponse.session_id}</div>}
              {fullResponse.error && <div style={{ color: '#ef4444' }}>Error: {fullResponse.error}</div>}
            </div>
          </div>
        )}
        
        {/* Timestamp */}
        <div style={{ fontSize: '11px', marginTop: '8px', opacity: 0.5 }}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
