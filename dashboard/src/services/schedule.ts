import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir, getFilePath } from './config.js';
import type { ScheduleData } from '../types.js';
import fs from 'fs';

const execAsync = promisify(exec);

export async function getScheduleData(): Promise<ScheduleData> {
  try {
    // Run schedule_day.py --json to get schedule data
    const { stdout, stderr } = await execAsync('python3 schedule_day.py --json', {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      console.error('Schedule system stderr:', stderr);
    }
    
    const data = JSON.parse(stdout);
    return data;
  } catch (error) {
    console.error('Error running schedule system:', error);
    
    // Fallback - try to load today_schedule.json if it exists
    try {
      const todaySchedulePath = getFilePath('today_schedule.json');
      const data = JSON.parse(fs.readFileSync(todaySchedulePath, 'utf8'));
      return {
        schedule: data.schedule || [],
        current_phase: data.current_phase || 'unknown'
      };
    } catch (fallbackError) {
      console.error('Error loading today_schedule.json:', fallbackError);
      return {
        schedule: [],
        current_phase: 'unknown'
      };
    }
  }
}