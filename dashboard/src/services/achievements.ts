import fs from 'fs';
import { getFilePath } from './config.js';
import type { AchievementsData, AllAchievements, Achievement } from '../types.js';

export function loadAllAchievements(): AllAchievements {
  try {
    const achievementsPath = getFilePath('achievements.json');
    const data = fs.readFileSync(achievementsPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading achievements:', error);
    return { achievements: {}, tiers: {} };
  }
}

export function loadEarnedAchievements(): AchievementsData {
  try {
    const earnedPath = getFilePath('achievements_earned.json');
    const data = fs.readFileSync(earnedPath, 'utf8');
    const parsed = JSON.parse(data);
    
    // Handle both old and new formats
    if (Array.isArray(parsed)) {
      // Old format - convert to new format
      return {
        earned: parsed,
        total_points: parsed.reduce((sum: number, achievement: Achievement) => sum + (achievement.points || 0), 0)
      };
    }
    
    // New format
    return parsed;
  } catch (error) {
    console.error('Error loading earned achievements:', error);
    return { earned: [], total_points: 0 };
  }
}

export function getAchievementsDashboardData() {
  const earned = loadEarnedAchievements();
  const allAchievements = loadAllAchievements();
  
  return {
    earned: earned.earned || [],
    total_points: earned.total_points || 0,
    all_achievements: allAchievements
  };
}