import fs from 'fs';
import path from 'path';
import type { HistoryEntry, StreamItem } from '../types.js';

const SESSIONS_DIR = path.join(
  process.env.HOME || '/home/hk',
  '.openclaw/agents/main/sessions'
);

export interface SessionLine {
  type: string;
  id?: string;
  parentId?: string | null;
  timestamp?: string;
  message?: {
    role: string;
    content: any;
    usage?: {
      input: number;
      output: number;
      totalTokens: number;
      cost?: { total: number };
    };
    model?: string;
    provider?: string;
    stopReason?: string;
    timestamp?: number;
  };
  customType?: string;
  data?: any;
  // session header fields
  version?: number;
  cwd?: string;
}

/**
 * Check if OpenClaw session logs are available
 */
export function hasSessionLogs(): boolean {
  try {
    return fs.existsSync(SESSIONS_DIR) &&
      fs.readdirSync(SESSIONS_DIR).some(f => f.endsWith('.jsonl'));
  } catch {
    return false;
  }
}

/**
 * Parse a single .jsonl session file into an array of typed lines
 */
function parseSessionFile(filePath: string): SessionLine[] {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines: SessionLine[] = [];
    for (const line of content.split('\n')) {
      if (!line.trim()) continue;
      try {
        lines.push(JSON.parse(line));
      } catch {
        // skip malformed lines
      }
    }
    return lines;
  } catch {
    return [];
  }
}

/**
 * Get all session files sorted by modification time (newest first)
 */
function getSessionFiles(limit?: number): string[] {
  try {
    const files = fs.readdirSync(SESSIONS_DIR)
      .filter(f => f.endsWith('.jsonl'))
      .map(f => ({
        name: f,
        path: path.join(SESSIONS_DIR, f),
        mtime: fs.statSync(path.join(SESSIONS_DIR, f)).mtimeMs
      }))
      .sort((a, b) => b.mtime - a.mtime);

    const selected = limit ? files.slice(0, limit) : files;
    return selected.map(f => f.path);
  } catch {
    return [];
  }
}

/**
 * Extract a text summary from assistant message content
 */
function extractTextFromContent(content: any): string {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) {
    const textParts = content
      .filter((c: any) => c.type === 'text' && c.text)
      .map((c: any) => c.text);
    return textParts.join(' ');
  }
  return '';
}

/**
 * Extract user message text from content
 */
function extractUserText(content: any): string {
  const text = extractTextFromContent(content);
  // Strip metadata prefix like "[Telegram User (@handle) ...]"
  const match = text.match(/\] (.+?)(?:\n|$)/);
  return match?.[1] ?? text.slice(0, 200);
}

/**
 * Count tool calls in assistant content
 */
function countToolCalls(content: any): number {
  if (!Array.isArray(content)) return 0;
  return content.filter((c: any) => c.type === 'toolCall').length;
}

/**
 * Load activity history derived from session logs.
 * Each session becomes one HistoryEntry.
 */
export function loadSessionHistory(limit = 100): HistoryEntry[] {
  const sessionFiles = getSessionFiles(limit);
  const entries: HistoryEntry[] = [];

  for (const filePath of sessionFiles) {
    const lines = parseSessionFile(filePath);
    if (lines.length === 0) continue;

    const header = lines.find(l => l.type === 'session');
    const timestamp = header?.timestamp || '';

    const userMessages = lines.filter(l => l.type === 'message' && l.message?.role === 'user');
    const assistantMessages = lines.filter(l => l.type === 'message' && l.message?.role === 'assistant');

    if (assistantMessages.length === 0) continue;

    // Summarize the session
    const firstUserMsg = userMessages[0]?.message;
    const firstUserText = firstUserMsg
      ? extractUserText(firstUserMsg.content)
      : 'Session activity';

    const totalToolCalls = assistantMessages.reduce(
      (sum, m) => sum + countToolCalls(m.message?.content), 0
    );

    const totalCost = assistantMessages.reduce((sum, m) => {
      return sum + (m.message?.usage?.cost?.total || 0);
    }, 0);

    const model = assistantMessages[0]?.message?.model || 'unknown';

    entries.push({
      timestamp: timestamp || '',
      thought: firstUserText.slice(0, 100),
      thought_id: path.basename(filePath, '.jsonl'),
      mood: model,
      summary: `${userMessages.length} messages, ${totalToolCalls} tool calls` +
        (totalCost > 0 ? ` ($${totalCost.toFixed(4)})` : ''),
      completed: true,
    });
  }

  return entries;
}

/**
 * Load stream items from session logs — individual messages as stream events
 */
export function loadSessionStream(limit = 50): StreamItem[] {
  const sessionFiles = getSessionFiles(20); // scan recent 20 sessions
  const items: StreamItem[] = [];

  for (const filePath of sessionFiles) {
    const lines = parseSessionFile(filePath);
    const sessionId = path.basename(filePath, '.jsonl');

    for (const line of lines) {
      if (line.type !== 'message') continue;
      const msg = line.message;
      if (!msg) continue;

      if (msg.role === 'user') {
        const text = extractUserText(msg.content);
        if (!text) continue;
        items.push({
          type: 'activity',
          timestamp: line.timestamp || '',
          thought_id: sessionId,
          mood: 'user',
          summary: `💬 ${text.slice(0, 150)}`,
          details: { role: 'user', model: null, session: sessionId }
        });
      } else if (msg.role === 'assistant') {
        const text = extractTextFromContent(msg.content);
        const toolCalls = countToolCalls(msg.content);
        const summary = toolCalls > 0
          ? `🔧 ${toolCalls} tool call${toolCalls > 1 ? 's' : ''}${text ? ': ' + text.slice(0, 100) : ''}`
          : `🤖 ${text.slice(0, 150) || '(thinking)'}`;

        items.push({
          type: 'activity',
          timestamp: line.timestamp || '',
          thought_id: sessionId,
          mood: msg.model || 'assistant',
          summary,
          details: {
            role: 'assistant',
            model: msg.model,
            cost: msg.usage?.cost?.total,
            tokens: msg.usage?.totalTokens,
            session: sessionId
          }
        });
      }
    }
  }

  // Sort newest first
  items.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  return items.slice(0, limit);
}

/**
 * Get session-based stats
 */
export function getSessionStats(): {
  totalSessions: number;
  totalMessages: number;
  totalToolCalls: number;
  totalCost: number;
  totalTokens: number;
  models: Record<string, number>;
} {
  const sessionFiles = getSessionFiles();
  let totalMessages = 0;
  let totalToolCalls = 0;
  let totalCost = 0;
  let totalTokens = 0;
  const models: Record<string, number> = {};

  for (const filePath of sessionFiles) {
    const lines = parseSessionFile(filePath);
    for (const line of lines) {
      if (line.type !== 'message') continue;
      const msg = line.message;
      if (!msg) continue;

      if (msg.role === 'user' || msg.role === 'assistant') {
        totalMessages++;
      }

      if (msg.role === 'assistant') {
        totalToolCalls += countToolCalls(msg.content);
        totalCost += msg.usage?.cost?.total || 0;
        totalTokens += msg.usage?.totalTokens || 0;

        if (msg.model) {
          models[msg.model] = (models[msg.model] || 0) + 1;
        }
      }
    }
  }

  return {
    totalSessions: sessionFiles.length,
    totalMessages,
    totalToolCalls,
    totalCost,
    totalTokens,
    models
  };
}
