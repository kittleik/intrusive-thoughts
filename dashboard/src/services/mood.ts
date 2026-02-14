import fs from 'fs';
import { getFilePath } from './config.js';
import type { Mood, TodayMood, MoodHistoryEntry, Soundtrack } from '../types.js';

export function loadMoods(): { base_moods: Mood[] } {
  try {
    const moodsPath = getFilePath('moods.json');
    const data = fs.readFileSync(moodsPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading moods:', error);
    return { base_moods: [] };
  }
}

export function loadTodayMood(): TodayMood | null {
  try {
    const todayMoodPath = getFilePath('today_mood.json');
    const data = fs.readFileSync(todayMoodPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading today mood:', error);
    return null;
  }
}

export function loadMoodHistory(): MoodHistoryEntry[] {
  try {
    const moodHistoryPath = getFilePath('mood_history.json');
    const data = fs.readFileSync(moodHistoryPath, 'utf8');
    const parsed = JSON.parse(data);
    return parsed.history || [];
  } catch (error) {
    console.error('Error loading mood history:', error);
    return [];
  }
}

export function loadSoundtracks(): Soundtrack {
  try {
    const soundtracksPath = getFilePath('soundtracks.json');
    const data = fs.readFileSync(soundtracksPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading soundtracks:', error);
    return { mood_soundtracks: {} };
  }
}

export function getCurrentMoodDisplay(): { mood_display: string; mood_description: string; today_soundtrack: string } {
  const todayMood = loadTodayMood();
  const soundtracks = loadSoundtracks();
  
  let mood_display = "🤔 Unknown";
  let mood_description = "";
  let today_soundtrack = "";
  
  if (todayMood) {
    const mood_id = todayMood.drifted_to || todayMood.id;
    const mood_emoji = todayMood.emoji;
    const mood_name = todayMood.name;
    mood_display = `${mood_emoji} ${mood_name}`;
    mood_description = todayMood.description || "";
    
    // Get soundtrack info
    const soundtrack_info = soundtracks.mood_soundtracks[mood_id];
    if (soundtrack_info) {
      const vibe = soundtrack_info.vibe_description || "";
      const genres = soundtrack_info.genres?.slice(0, 3).join(", ") || "";
      today_soundtrack = `${vibe} — ${genres}`;
    }
  }
  
  return { mood_display, mood_description, today_soundtrack };
}