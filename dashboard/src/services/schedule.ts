import fs from 'fs';
import path from 'path';
import type { ScheduleData } from '../types.js';

const OPENCLAW_CRON_PATH = path.join(process.env.HOME || '/home/hk', '.openclaw/cron/jobs.json');

interface CronJob {
  id: string;
  name?: string;
  schedule: { kind: string; expr?: string; everyMs?: number; at?: string };
  payload: { kind: string; text?: string; message?: string };
  enabled: boolean;
  lastRun?: string;
  lastStatus?: string;
  nextRun?: string;
}

export async function getScheduleData(): Promise<ScheduleData> {
  try {
    // Read actual OpenClaw cron jobs
    const raw = fs.readFileSync(OPENCLAW_CRON_PATH, 'utf-8');
    const parsed = JSON.parse(raw);
    const jobs: CronJob[] = Array.isArray(parsed) ? parsed : (parsed.jobs || []);
    
    // Filter to intrusive-thoughts related jobs
    const itJobs = jobs.filter(j => {
      const text = (j.payload?.text || j.payload?.message || j.name || '').toLowerCase();
      return text.includes('mood') || text.includes('intrusive') || text.includes('night') || 
             text.includes('workshop') || text.includes('drift') || text.includes('pop-in') ||
             text.includes('morning') || text.includes('thought');
    });
    
    const schedule = itJobs.map(j => {
      const state = (j as any).state || {};
      return {
        id: j.id,
        name: j.name || 'Unnamed job',
        schedule_type: j.schedule.kind,
        schedule_expr: j.schedule.expr || (j.schedule.everyMs ? `every ${j.schedule.everyMs/60000}min` : j.schedule.at || ''),
        enabled: j.enabled,
        last_run: state.lastRunAtMs ? new Date(state.lastRunAtMs).toISOString() : null,
        last_status: state.lastStatus || null,
        last_duration_ms: state.lastDurationMs || null,
        next_run: state.nextRunAtMs ? new Date(state.nextRunAtMs).toISOString() : null,
        consecutive_errors: state.consecutiveErrors || 0,
        delete_after_run: (j as any).deleteAfterRun || false
      };
    });
    
    // Sort by next run time (soonest first), enabled before disabled
    schedule.sort((a, b) => {
      const aNext = a.next_run ? new Date(a.next_run).getTime() : Infinity;
      const bNext = b.next_run ? new Date(b.next_run).getTime() : Infinity;
      return aNext - bNext;
    });

    return {
      schedule,
      current_phase: getCurrentPhase()
    };
  } catch (error) {
    console.error('Error reading OpenClaw cron jobs:', error);
    return { schedule: [], current_phase: getCurrentPhase() };
  }
}

function getCurrentPhase(): string {
  const hour = new Date().getHours();
  if (hour >= 3 && hour < 7) return 'night_workshop';
  if (hour >= 7 && hour < 9) return 'morning_ritual';
  if (hour >= 9 && hour < 23) return 'daytime';
  return 'quiet_hours';
}
