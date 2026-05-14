import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface UserPublic {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  data?: UserPublic[];
  intent?: string;
  timestamp: number;
}

export interface QueryRequest {
  query: string;
  limit?: number;
  provider: 'google' | 'openrouter';
  session_id?: string;
}

export interface QueryResponse {
  summary: string;
  intent: string;
  data: UserPublic[];
  filters: Record<string, unknown>;
  count: number;
  error: string | null;
  session_id: string | null;
}

function getUserId(): string {
  if (typeof window === 'undefined') return 'default';
  
  let userId = localStorage.getItem('chat_user_id');
  if (!userId) {
    userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    localStorage.setItem('chat_user_id', userId);
  }
  return userId;
}

function getSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('chat_session_id');
}

function setSessionId(sessionId: string | null): void {
  if (typeof window === 'undefined') return;
  if (sessionId) {
    localStorage.setItem('chat_session_id', sessionId);
  } else {
    localStorage.removeItem('chat_session_id');
  }
}

export async function sendMessage(
  message: string,
  provider: 'google' | 'openrouter' = 'openrouter',
  limit: number = 20
): Promise<{ response: QueryResponse; messages: ChatMessage[] }> {
  const userId = getUserId();
  const sessionId = getSessionId();

  const request: QueryRequest = {
    query: message,
    provider,
    limit,
    session_id: sessionId || undefined,
  };

  const response = await axios.post<QueryResponse>(
    API_BASE_URL + '/api/v1/agents/users/query',
    request,
    {
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId,
      },
    }
  );

  const data = response.data;

  if (data.session_id) {
    setSessionId(data.session_id);
  }

  const assistantMessage: ChatMessage = {
    id: 'msg_' + Date.now(),
    role: 'assistant',
    content: data.summary,
    data: data.data,
    intent: data.intent,
    timestamp: Date.now(),
  };

  return {
    response: data,
    messages: [assistantMessage],
  };
}

export function clearSession(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('chat_session_id');
}
