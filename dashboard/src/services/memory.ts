import fs from 'fs';
import path from 'path';
import os from 'os';
import { getDataDir } from './config.js';
import type { MemoryData } from '../types.js';

export function loadMemoryData(): MemoryData {
  try {
    // Check OpenClaw's native memory system instead of old memory_store
    const openclawMemoryDir = path.join(os.homedir(), '.openclaw', 'workspace', 'memory');
    const memoryMdPath = path.join(os.homedir(), '.openclaw', 'workspace', 'MEMORY.md');
    const moodPatternsPath = path.join(getDataDir(), 'mood_patterns.md');
    
    const memoryData: MemoryData = {};
    let totalEntries = 0;
    
    // Check OpenClaw MEMORY.md
    if (fs.existsSync(memoryMdPath)) {
      try {
        const content = fs.readFileSync(memoryMdPath, 'utf8');
        memoryData.long_term_memory = {
          size: content.length,
          last_updated: fs.statSync(memoryMdPath).mtime,
          status: 'available'
        };
        totalEntries += 1;
      } catch (error) {
        memoryData.long_term_memory = { status: 'error', error: error.toString() };
      }
    } else {
      memoryData.long_term_memory = { status: 'missing' };
    }
    
    // Check daily memory files
    if (fs.existsSync(openclawMemoryDir)) {
      try {
        const files = fs.readdirSync(openclawMemoryDir);
        const dailyFiles = files.filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/));
        memoryData.daily_memories = {
          count: dailyFiles.length,
          files: dailyFiles.sort().reverse().slice(0, 10), // Most recent 10
          status: 'available'
        };
        totalEntries += dailyFiles.length;
      } catch (error) {
        memoryData.daily_memories = { status: 'error', error: error.toString() };
      }
    } else {
      memoryData.daily_memories = { status: 'missing' };
    }
    
    // Check mood patterns markdown
    if (fs.existsSync(moodPatternsPath)) {
      try {
        const content = fs.readFileSync(moodPatternsPath, 'utf8');
        const moodEntries = (content.match(/^## \d{4}-\d{2}-\d{2}/gm) || []).length;
        memoryData.mood_patterns = {
          entries: moodEntries,
          last_updated: fs.statSync(moodPatternsPath).mtime,
          status: 'available'
        };
        totalEntries += moodEntries;
      } catch (error) {
        memoryData.mood_patterns = { status: 'error', error: error.toString() };
      }
    } else {
      memoryData.mood_patterns = { status: 'missing' };
    }
    
    memoryData.total_entries = totalEntries;
    memoryData.recent_activity = getRecentMemoryActivity();
    
    return memoryData;
  } catch (error) {
    console.error('Error loading memory data:', error);
    return { error: 'memory system unavailable' };
  }
}

function getRecentMemoryActivity(): string {
  try {
    const openclawMemoryDir = path.join(os.homedir(), '.openclaw', 'workspace', 'memory');
    const memoryMdPath = path.join(os.homedir(), '.openclaw', 'workspace', 'MEMORY.md');
    
    let mostRecentTime = 0;
    let mostRecentFile = '';
    
    // Check MEMORY.md
    if (fs.existsSync(memoryMdPath)) {
      const stats = fs.statSync(memoryMdPath);
      if (stats.mtime.getTime() > mostRecentTime) {
        mostRecentTime = stats.mtime.getTime();
        mostRecentFile = 'MEMORY.md';
      }
    }
    
    // Check daily memory files
    if (fs.existsSync(openclawMemoryDir)) {
      const files = fs.readdirSync(openclawMemoryDir);
      for (const file of files) {
        if (file.endsWith('.md')) {
          const filePath = path.join(openclawMemoryDir, file);
          const stats = fs.statSync(filePath);
          if (stats.mtime.getTime() > mostRecentTime) {
            mostRecentTime = stats.mtime.getTime();
            mostRecentFile = file;
          }
        }
      }
    }
    
    if (mostRecentFile) {
      const timeDiff = Date.now() - mostRecentTime;
      const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));
      return `${mostRecentFile} updated ${hoursAgo}h ago`;
    }
    
    return 'No recent activity';
  } catch (error) {
    return 'Unknown';
  }
}

// OpenClaw native memory interface
export async function getMemorySystemDashboardData(): Promise<MemoryData> {
  try {
    return loadMemoryData();
  } catch (error) {
    console.error('Error getting memory system dashboard data:', error);
    return { error: 'memory system unavailable' };
  }
}