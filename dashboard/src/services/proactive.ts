import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir } from './config.js';
import type { ProactiveData } from '../types.js';

const execAsync = promisify(exec);

export function loadWalData(): any[] {
  try {
    const walDir = path.join(getDataDir(), 'wal');
    
    if (!fs.existsSync(walDir)) {
      return [];
    }
    
    const walEntries = [];
    const files = fs.readdirSync(walDir).filter(f => f.endsWith('.json'));
    
    // Sort files by name (should be chronological) and get recent ones
    for (const file of files.sort().slice(-20)) {
      try {
        const filePath = path.join(walDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        walEntries.push({ file, ...data });
      } catch (error) {
        console.error(`Error loading wal file ${file}:`, error);
      }
    }
    
    return walEntries;
  } catch (error) {
    console.error('Error loading wal data:', error);
    return [];
  }
}

export async function getProactiveSystemData(): Promise<ProactiveData> {
  try {
    // Try to call proactive.py dashboard function
    const { stdout, stderr } = await execAsync('python3 -c "from proactive import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      console.error('Proactive system stderr:', stderr);
    }
    
    return JSON.parse(stdout);
  } catch (error) {
    console.error('Error running proactive system:', error);
    
    // Fallback to loading wal files directly
    const walData = loadWalData();
    
    return {
      wal_entries: walData,
      total_entries: walData.length,
      recent_activity: walData.length > 0 ? `${walData.length} entries` : 'No recent activity'
    };
  }
}

export async function getProactiveDashboardData(): Promise<ProactiveData> {
  const systemData = await getProactiveSystemData();
  
  if (systemData.error) {
    const walData = loadWalData();
    return {
      wal_entries: walData,
      total_entries: walData.length,
      recent_activity: walData.length > 0 ? `${walData.length} entries` : 'No recent activity',
      error: 'proactive system unavailable'
    };
  }
  
  return systemData;
}