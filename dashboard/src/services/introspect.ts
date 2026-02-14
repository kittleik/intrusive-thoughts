import { exec } from 'child_process';
import { promisify } from 'util';
import { getDataDir } from './config.js';
import type { IntrospectionData, SystemExplanation, DecisionTrace } from '../types.js';

const execAsync = promisify(exec);

export async function runIntrospect(): Promise<IntrospectionData> {
  try {
    const { stdout, stderr } = await execAsync('python3 introspect.py', {
      cwd: getDataDir(),
      timeout: 10000
    });
    
    if (stderr) {
      console.error('Introspect stderr:', stderr);
    }
    
    return JSON.parse(stdout);
  } catch (error) {
    console.error('Error running introspect:', error);
    return { error: `Failed to run introspect: ${error}` };
  }
}

export async function runExplainSystem(systemName: string): Promise<SystemExplanation> {
  try {
    const { stdout, stderr } = await execAsync(`python3 explain_system.py ${systemName}`, {
      cwd: getDataDir(),
      timeout: 10000
    });
    
    if (stderr) {
      return {
        error: `System '${systemName}' not found or error occurred`,
        stderr: stderr
      };
    }
    
    return {
      output: stdout,
      system: systemName
    };
  } catch (error) {
    console.error(`Error explaining ${systemName}:`, error);
    return { error: `Failed to explain ${systemName}: ${error}` };
  }
}

export async function runDecisionTrace(): Promise<DecisionTrace> {
  try {
    const { stdout, stderr } = await execAsync('python3 decision_trace.py', {
      cwd: getDataDir(),
      timeout: 10000
    });
    
    if (stderr) {
      return {
        error: 'No recent decisions found',
        stderr: stderr
      };
    }
    
    return {
      output: stdout
    };
  } catch (error) {
    console.error('Error tracing decision:', error);
    return { error: `Failed to trace decision: ${error}` };
  }
}