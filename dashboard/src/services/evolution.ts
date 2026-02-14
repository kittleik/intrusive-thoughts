import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir } from './config.js';
import type { EvolutionData } from '../types.js';

const execAsync = promisify(exec);

export function loadEvolutionData(): EvolutionData {
  try {
    const evolutionDir = path.join(getDataDir(), 'evolution');
    
    if (!fs.existsSync(evolutionDir)) {
      return { error: 'evolution directory not found' };
    }
    
    const evolutionData: EvolutionData = {};
    const files = fs.readdirSync(evolutionDir);
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const filePath = path.join(evolutionDir, file);
          const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
          const key = file.replace('.json', '');
          evolutionData[key] = data;
        } catch (error) {
          console.error(`Error loading evolution file ${file}:`, error);
        }
      }
    }
    
    return evolutionData;
  } catch (error) {
    console.error('Error loading evolution data:', error);
    return { error: 'evolution system unavailable' };
  }
}

export async function getEvolutionSystemData(): Promise<EvolutionData> {
  try {
    // Try to call self_evolution.py dashboard function
    const { stdout, stderr } = await execAsync('python3 -c "from self_evolution import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      console.error('Evolution system stderr:', stderr);
    }
    
    return JSON.parse(stdout);
  } catch (error) {
    console.error('Error running evolution system:', error);
    
    // Fallback to loading evolution files directly
    return loadEvolutionData();
  }
}

export async function getEvolutionDashboardData(): Promise<EvolutionData> {
  const systemData = await getEvolutionSystemData();
  
  if (systemData.error) {
    return loadEvolutionData();
  }
  
  return systemData;
}