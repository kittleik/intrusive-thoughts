import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir } from './config.js';
import type { TrustData } from '../types.js';

const execAsync = promisify(exec);

export function loadTrustStoreData(): TrustData {
  try {
    const trustStoreDir = path.join(getDataDir(), 'trust_store');
    
    if (!fs.existsSync(trustStoreDir)) {
      return { error: 'trust store directory not found' };
    }
    
    const trustData: TrustData = {};
    const files = fs.readdirSync(trustStoreDir);
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const filePath = path.join(trustStoreDir, file);
          const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          const key = file.replace('.json', '');
          trustData[key] = data;
        } catch (error) {
          console.error(`Error loading trust file ${file}:`, error);
        }
      }
    }
    
    return trustData;
  } catch (error) {
    console.error('Error loading trust store data:', error);
    return { error: 'trust system unavailable' };
  }
}

export async function getTrustSystemStats(): Promise<TrustData> {
  try {
    // Try to run trust_system.py get_stats
    const { stdout, stderr } = await execAsync('python3 trust_system.py get_stats', {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      console.error('Trust system stderr:', stderr);
    }
    
    // Try to parse JSON output
    try {
      return JSON.parse(stdout);
    } catch {
      // If not JSON, wrap in object
      return {
        trust_score: 'unknown',
        status: stdout.trim() || 'unknown',
        raw_output: stdout
      };
    }
  } catch (error) {
    console.error('Error running trust system:', error);
    
    // Fallback to loading trust store files directly
    return loadTrustStoreData();
  }
}

export async function getTrustDashboardData(): Promise<TrustData> {
  // Try to get stats via subprocess first, then fallback to direct file reading
  const stats = await getTrustSystemStats();
  
  if (stats.error) {
    return loadTrustStoreData();
  }
  
  return stats;
}