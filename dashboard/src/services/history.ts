import fs from 'fs';
import path from 'path';
import { getFilePath, getDataDir } from './config.js';
import { hasSessionLogs, loadSessionHistory } from './sessions.js';
import type { HistoryEntry, PickEntry, RejectionEntry, StreamItem } from '../types.js';

/**
 * Load history from OpenClaw session logs, falling back to history.json
 */
export function loadHistory(): HistoryEntry[] {
  // Try session logs first
  if (hasSessionLogs()) {
    try {
      const entries = loadSessionHistory();
      if (entries.length > 0) return entries;
    } catch (error) {
      console.error('Error loading session history, falling back to history.json:', error);
    }
  }

  // Fallback to history.json
  try {
    const historyPath = getFilePath('history.json');
    const data = fs.readFileSync(historyPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading history:', error);
    return [];
  }
}

export function loadPicks(): PickEntry[] {
  try {
    const picksLogPath = path.join(getDataDir(), 'data', 'log', 'picks.log');
    const lines = fs.readFileSync(picksLogPath, 'utf8').split('\n').filter(line => line.trim());

    const picks: PickEntry[] = [];
    for (const line of lines) {
      const parts = line.split(' | ');
      if (parts.length >= 1) {
        const timestamp = parts[0];
        const meta: Record<string, any> = { timestamp };

        // Parse metadata from remaining parts
        for (let i = 1; i < parts.length; i++) {
          const part = parts[i];
          if (part && part.includes('=')) {
            const [key, value] = part.split('=', 2);
            if (key && value !== undefined) {
              meta[key] = value;
            }
          }
        }

        picks.push(meta as PickEntry);
      }
    }

    return picks;
  } catch (error) {
    console.error('Error loading picks:', error);
    return [];
  }
}

export function loadRejections(): RejectionEntry[] {
  try {
    const rejectionsLogPath = path.join(getDataDir(), 'data', 'log', 'rejections.log');
    const lines = fs.readFileSync(rejectionsLogPath, 'utf8').split('\n').filter(line => line.trim());

    const rejections: RejectionEntry[] = [];
    for (const line of lines) {
      const parts = line.split(' | ');
      if (parts.length >= 5) {
        rejections.push({
          timestamp: parts[0] || '',
          thought_id: parts[1] || '', 
          mood: parts[2] || '',
          reason: parts[3] || '',
          flavor_text: parts[4] || ''
        });
      }
    }

    return rejections;
  } catch (error) {
    console.error('Error loading rejections:', error);
    return [];
  }
}

export function loadDecisions(): any[] {
  try {
    const decisionsPath = path.join(getDataDir(), 'data', 'log', 'decisions.json');
    const data = fs.readFileSync(decisionsPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading decisions:', error);
    return [];
  }
}

export function loadStreamData(limit = 50): StreamItem[] {
  const streamItems: StreamItem[] = [];

  // Only use intrusive-thoughts own data (history.json), NOT OpenClaw session logs
  const history = loadHistory();
  for (const entry of history.slice(-limit)) {
    streamItems.push({
      type: entry.type || 'activity',
      timestamp: entry.timestamp || '',
      thought_id: entry.thought_id || 'unknown',
      mood: entry.mood || 'unknown',
      summary: entry.summary || `Completed ${entry.thought_id}`,
      details: entry
    });
  }

  // Add picks
  const picks = loadPicks();
  for (const pick of picks.slice(-limit)) {
    streamItems.push({
      type: 'pick',
      timestamp: pick.timestamp || '',
      thought_id: pick.thought || 'unknown',
      mood: pick.today_mood || 'unknown',
      summary: `Picked ${pick.thought || 'unknown'} thought`,
      details: pick
    });
  }

  // Add rejections
  const rejections = loadRejections();
  for (const rejection of rejections.slice(-limit)) {
    streamItems.push({
      type: 'rejection',
      timestamp: rejection.timestamp || '',
      thought_id: rejection.thought_id || 'unknown',
      mood: rejection.mood || 'unknown',
      summary: `Rejected ${rejection.thought_id || 'unknown'}: ${rejection.reason || 'no reason'}`,
      details: rejection
    });
  }

  // Add mood drifts from today_mood.json activity_log
  try {
    const todayMoodPath = getFilePath('today_mood.json');
    const todayMoodData = JSON.parse(fs.readFileSync(todayMoodPath, 'utf8'));

    if (todayMoodData && todayMoodData.activity_log) {
      for (const activity of todayMoodData.activity_log.slice(-limit)) {
        streamItems.push({
          type: 'mood_drift',
          timestamp: activity.time || '',
          mood: activity.action?.to || 'unknown',
          summary: `Mood drift: ${activity.action?.from || '?'} → ${activity.action?.to || '?'}`,
          details: activity
        });
      }
    }
  } catch (error) {
    console.error('Error loading mood drift data:', error);
  }

  // Sort by timestamp (most recent first)
  streamItems.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
  return streamItems.slice(0, limit);
}