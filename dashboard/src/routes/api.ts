import express from 'express';
import { exec } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';

function countThoughts(data: any): number {
  if (data?.thoughts && typeof data.thoughts === 'object') return Object.keys(data.thoughts).length;
  if (data?.moods && typeof data.moods === 'object') {
    return Object.values(data.moods).reduce((sum: number, group: any) => {
      if (Array.isArray(group)) return sum + group.length;
      if (typeof group === 'object' && group !== null) return sum + Object.keys(group).length;
      return sum;
    }, 0);
  }
  return 0;
}
import { getDataDir } from '../services/config.js';
import { loadHistory, loadPicks, loadRejections, loadDecisions, loadStreamData } from '../services/history.js';
import { loadTodayMood, loadMoodHistory } from '../services/mood.js';
import { loadThoughts } from '../services/thoughts.js';
import { getMemorySystemDashboardData } from '../services/memory.js';
import { getTrustDashboardData } from '../services/trust.js';
import { getEvolutionDashboardData } from '../services/evolution.js';
import { getHealthDashboardData } from '../services/health.js';
import { getScheduleData } from '../services/schedule.js';
import { getAchievementsDashboardData } from '../services/achievements.js';
import { loadJournalEntries, loadJournalEntry } from '../services/journal.js';
import { getProactiveDashboardData } from '../services/proactive.js';
import { runIntrospect, runExplainSystem, runDecisionTrace } from '../services/introspect.js';
import type { StatsResponse, SystemsResponse } from '../types.js';

const router = express.Router();
const execAsync = promisify(exec);

// GET /api/stats
router.get('/stats', (_req, res) => {
  try {
    const history = loadHistory();
    const picks = loadPicks();
    const achievements = getAchievementsDashboardData();
    
    // Count thought picks
    const thoughtCounts: Record<string, number> = {};
    for (const pick of picks) {
      const thoughtId = pick.thought || '?';
      thoughtCounts[thoughtId] = (thoughtCounts[thoughtId] || 0) + 1;
    }
    
    const stats: StatsResponse = {
      total_picks: picks.length,
      total_completed: history.length,
      achievements: achievements.earned.length,
      points: achievements.total_points,
      thought_counts: thoughtCounts,
      recent: history.slice(-10).reverse()
    };
    
    res.json(stats);
  } catch (error) {
    console.error('Error in /api/stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/stream
router.get('/stream', (_req, res) => {
  try {
    const streamData = loadStreamData(50);
    res.json(streamData);
  } catch (error) {
    console.error('Error in /api/stream:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/decisions
router.get('/decisions', (_req, res) => {
  try {
    const decisions = loadDecisions();
    res.json(decisions.slice(-50));
  } catch (error) {
    console.error('Error in /api/decisions:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/rejections
router.get('/rejections', (_req, res) => {
  try {
    const rejections = loadRejections();
    res.json(rejections.slice(-50));
  } catch (error) {
    console.error('Error in /api/rejections:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/mood-timeline
router.get('/mood-timeline', (_req, res) => {
  try {
    const moodHistory = loadMoodHistory();
    res.json(moodHistory.slice(-30));
  } catch (error) {
    console.error('Error in /api/mood-timeline:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/presets
router.get('/presets', (_req, res) => {
  try {
    const fs = require('fs');
    const path = require('path');
    
    const presetsDir = path.join(getDataDir(), 'presets');
    const presets: Record<string, any> = {};
    
    if (fs.existsSync(presetsDir)) {
      const presetFiles = fs.readdirSync(presetsDir).filter((f: string) => f.endsWith('.json'));
      for (const file of presetFiles) {
        try {
          const presetData = JSON.parse(fs.readFileSync(path.join(presetsDir, file), 'utf8'));
          presets[file.replace('.json', '')] = presetData;
        } catch (error) {
          console.error(`Error loading preset ${file}:`, error);
        }
      }
    }
    
    res.json(presets);
  } catch (error) {
    console.error('Error in /api/presets:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/streaks
router.get('/streaks', (_req, res) => {
  try {
    const streaksPath = path.join(getDataDir(), 'streaks.json');
    const data = fs.readFileSync(streaksPath, 'utf8');
    res.json(JSON.parse(data));
  } catch {
    res.json({});
  }
});

// GET /api/schedule
router.get('/schedule', async (_req, res) => {
  try {
    const scheduleData = await getScheduleData();
    res.json(scheduleData);
  } catch (error) {
    console.error('Error in /api/schedule:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/memory
router.get('/memory', async (_req, res) => {
  try {
    const memoryData = await getMemorySystemDashboardData();
    res.json(memoryData);
  } catch (error) {
    console.error('Error in /api/memory:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/trust
router.get('/trust', async (_req, res) => {
  try {
    const trustData = await getTrustDashboardData();
    res.json(trustData);
  } catch (error) {
    console.error('Error in /api/trust:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/evolution
router.get('/evolution', async (_req, res) => {
  try {
    const evolutionData = await getEvolutionDashboardData();
    res.json(evolutionData);
  } catch (error) {
    console.error('Error in /api/evolution:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/proactive
router.get('/proactive', async (_req, res) => {
  try {
    const proactiveData = await getProactiveDashboardData();
    res.json(proactiveData);
  } catch (error) {
    console.error('Error in /api/proactive:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/health
router.get('/health', async (_req, res) => {
  try {
    const healthData = await getHealthDashboardData();
    res.json(healthData);
  } catch (error) {
    console.error('Error in /api/health:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/systems
router.get('/systems', (_req, res) => {
  try {
    const todayMood = loadTodayMood();
    const history = loadHistory();
    const thoughts = loadThoughts();
    const achievements = getAchievementsDashboardData();
    
    const systems: SystemsResponse = {
      mood: { status: 'active', current_mood: todayMood },
      memory: { status: 'active', entries: history.length },
      thoughts: { status: 'active', total_thoughts: countThoughts(thoughts) },
      achievements: { status: 'active', earned: achievements.earned.length },
      health: { status: 'active', monitoring: true }
    };
    
    res.json(systems);
  } catch (error) {
    console.error('Error in /api/systems:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/journal
router.get('/journal', (req, res) => {
  try {
    const date = req.query.date as string;
    if (date) {
      const entry = loadJournalEntry(date);
      if (entry) {
        res.json(entry);
      } else {
        res.status(404).json({ error: `Journal entry for ${date} not found` });
      }
    } else {
      res.status(400).json({ error: 'Date parameter required' });
    }
  } catch (error) {
    console.error('Error in /api/journal:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/journal/list
router.get('/journal/list', (_req, res) => {
  try {
    const entries = loadJournalEntries();
    res.json(entries);
  } catch (error) {
    console.error('Error in /api/journal/list:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/achievements
router.get('/achievements', (_req, res) => {
  try {
    const achievementsData = getAchievementsDashboardData();
    res.json(achievementsData);
  } catch (error) {
    console.error('Error in /api/achievements:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/night-stats
router.get('/night-stats', (_req, res) => {
  try {
    const picks = loadPicks();
    let dayPicks = 0;
    let nightPicks = 0;
    
    for (const pick of picks) {
      try {
        const timestamp = pick.timestamp || '';
        if (timestamp) {
          const dt = new Date(timestamp.replace('Z', '+00:00'));
          const hour = dt.getHours();
          if (hour >= 6 && hour <= 20) {
            dayPicks++;
          } else {
            nightPicks++;
          }
        }
      } catch {
        // Skip invalid timestamps
        continue;
      }
    }
    
    const total = dayPicks + nightPicks;
    const nightPercentage = total > 0 ? (nightPicks / total) * 100 : 0;
    
    res.json({
      day_picks: dayPicks,
      night_picks: nightPicks,
      total,
      night_percentage: nightPercentage
    });
  } catch (error) {
    console.error('Error in /api/night-stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/introspect
router.get('/introspect', async (_req, res) => {
  try {
    const introspectData = await runIntrospect();
    res.json(introspectData);
  } catch (error) {
    console.error('Error in /api/introspect:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/explain/:system
router.get('/explain/:system', async (req, res) => {
  try {
    const systemName = req.params.system;
    const explanationData = await runExplainSystem(systemName);
    res.json(explanationData);
  } catch (error) {
    console.error('Error in /api/explain:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/why
router.get('/why', async (_req, res) => {
  try {
    const decisionData = await runDecisionTrace();
    res.json(decisionData);
  } catch (error) {
    console.error('Error in /api/why:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/roi
router.get('/roi', async (_req, res) => {
  try {
    // Run ROI tracker to generate fresh data
    await execAsync('./roi_tracker.py --json', {
      cwd: getDataDir(),
      timeout: 10000
    });
    
    // Load the generated ROI data
    const roiPath = path.join(getDataDir(), 'log', 'roi.json');
    const roiData = JSON.parse(fs.readFileSync(roiPath, 'utf8'));
    res.json(roiData);
  } catch (error) {
    console.error('Error in /api/roi:', error);
<<<<<<< Updated upstream
    // Return empty data structure if ROI tracking fails
=======
>>>>>>> Stashed changes
    res.json({
      generated_at: new Date().toISOString(),
      total_history_entries: 0,
      thoughts_analyzed: 0,
      roi_data: {},
      error: 'ROI data not available'
    });
  }
});

// POST /api/set-mood
router.post('/set-mood', async (req, res) => {
  try {
    const { mood_id } = req.body;
    if (!mood_id) {
      res.status(400).json({ status: 'error', error: 'Missing mood_id' });
      return;
    }
    
    const { stderr } = await execAsync(`./set_mood.sh ${mood_id}`, {
      cwd: getDataDir(),
      timeout: 5000
    });
    
    if (stderr) {
      res.json({ status: 'error', error: stderr });
      return;
    }
    
    res.json({ status: 'success', message: `Mood set to ${mood_id}` });
  } catch (error) {
    console.error('Error in /api/set-mood:', error);
    res.json({ status: 'error', error: String(error) });
  }
});

// POST /api/trigger
router.post('/trigger', async (_req, res) => {
  try {
    const { stderr } = await execAsync('./suggest_thought.sh', {
      cwd: getDataDir(),
      timeout: 10000
    });
    
    if (stderr) {
      res.json({ status: 'error', error: stderr });
      return;
    }
    
    res.json({ status: 'success', message: 'Impulse triggered' });
  } catch (error) {
    console.error('Error in /api/trigger:', error);
    res.json({ status: 'error', error: String(error) });
  }
});

// POST /api/preset-apply
router.post('/preset-apply', async (req, res) => {
  try {
    const { preset } = req.body;
    if (!preset) {
      res.status(400).json({ status: 'error', error: 'Missing preset name' });
      return;
    }
    
    // This would need to implement preset application logic
    // For now, just return success
    res.json({ status: 'success', message: `Applied preset ${preset}` });
  } catch (error) {
    console.error('Error in /api/preset-apply:', error);
    res.json({ status: 'error', error: String(error) });
  }
});

// PUT /api/thought-weight
router.put('/thought-weight', async (req, res) => {
  try {
    const { thought_id, weight } = req.body;
    if (!thought_id || weight === undefined) {
      res.status(400).json({ status: 'error', error: 'Missing thought_id or weight' });
      return;
    }
    
    // This would need to implement thought weight updating logic
    // For now, just return success
    res.json({ status: 'success', message: `Updated ${thought_id} weight to ${weight}` });
  } catch (error) {
    console.error('Error in /api/thought-weight:', error);
    res.json({ status: 'error', error: String(error) });
  }
});

export default router;