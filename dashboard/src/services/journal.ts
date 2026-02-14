import fs from 'fs';
import path from 'path';
import { getDataDir } from './config.js';
import type { JournalEntry } from '../types.js';

export function loadJournalEntries(limit?: number): JournalEntry[] {
  try {
    const journalDir = path.join(getDataDir(), 'journal');
    
    if (!fs.existsSync(journalDir)) {
      return [];
    }
    
    const entries: JournalEntry[] = [];
    const files = fs.readdirSync(journalDir).filter(f => f.endsWith('.md'));
    
    for (const file of files) {
      try {
        const filePath = path.join(journalDir, file);
        const content = fs.readFileSync(filePath, 'utf8');
        
        entries.push({
          date: file.replace('.md', ''),
          filename: file,
          content,
          preview: content.length > 300 ? content.substring(0, 300) + '...' : content,
          word_count: content.split(/\s+/).length
        });
      } catch (error) {
        console.error(`Error loading journal file ${file}:`, error);
      }
    }
    
    // Sort by date (most recent first)
    entries.sort((a, b) => b.date.localeCompare(a.date));
    
    if (limit) {
      return entries.slice(0, limit);
    }
    
    return entries;
  } catch (error) {
    console.error('Error loading journal entries:', error);
    return [];
  }
}

export function loadJournalEntry(date: string): JournalEntry | null {
  try {
    const journalDir = path.join(getDataDir(), 'journal');
    const filePath = path.join(journalDir, `${date}.md`);
    
    if (!fs.existsSync(filePath)) {
      return null;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    return {
      date,
      filename: `${date}.md`,
      content,
      preview: content.length > 300 ? content.substring(0, 300) + '...' : content,
      word_count: content.split(/\s+/).length
    };
  } catch (error) {
    console.error(`Error loading journal entry for ${date}:`, error);
    return null;
  }
}