import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir } from './config.js';
import type { HealthData } from '../types.js';

const execAsync = promisify(exec);

export function loadHealthStatusData(): HealthData {
  try {
    const healthDir = path.join(getDataDir(), 'health');
    const statusPath = path.join(healthDir, 'status.json');
    
    if (!fs.existsSync(statusPath)) {
      return { error: 'health status file not found' };
    }
    
    const data = JSON.parse(fs.readFileSync(statusPath, 'utf8'));
    return data;
  } catch (error) {
    console.error('Error loading health status:', error);
    return { error: 'health status unavailable' };
  }
}

export function loadHeartbeatData(): any[] {
  try {
    const healthDir = path.join(getDataDir(), 'health');
    const heartbeatFiles = fs.readdirSync(healthDir).filter(f => f.startsWith('heartbeat') && f.endsWith('.json'));
    
    const heartbeats = [];
    for (const file of heartbeatFiles.sort().slice(-10)) { // Get last 10 heartbeat files
      try {
        const filePath = path.join(healthDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        heartbeats.push({ file, ...data });
      } catch (error) {
        console.error(`Error loading heartbeat file ${file}:`, error);
      }
    }
    
    return heartbeats;
  } catch (error) {
    console.error('Error loading heartbeat data:', error);
    return [];
  }
}

export async function getHealthMonitorData(): Promise<HealthData> {
  try {
    // Try to call health_monitor.py dashboard function
    const { stdout, stderr } = await execAsync('python3 -c "from health_monitor import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      console.error('Health monitor stderr:', stderr);
    }
    
    return JSON.parse(stdout);
  } catch (error) {
    console.error('Error running health monitor:', error);
    
    // Fallback to loading health files directly
    const statusData = loadHealthStatusData();
    const heartbeats = loadHeartbeatData();
    
    return {
      status: statusData,
      heartbeats,
      error: statusData.error
    };
  }
}

export async function getHealthDashboardData(): Promise<HealthData> {
  return await getHealthMonitorData();
}