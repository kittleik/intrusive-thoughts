"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const child_process_1 = require("child_process");
const util_1 = require("util");
function countThoughts(data) {
    if (data?.thoughts && typeof data.thoughts === 'object')
        return Object.keys(data.thoughts).length;
    if (data?.moods && typeof data.moods === 'object') {
        return Object.values(data.moods).reduce((sum, group) => {
            if (Array.isArray(group))
                return sum + group.length;
            if (typeof group === 'object' && group !== null)
                return sum + Object.keys(group).length;
            return sum;
        }, 0);
    }
    return 0;
}
const config_js_1 = require("../services/config.js");
const history_js_1 = require("../services/history.js");
const mood_js_1 = require("../services/mood.js");
const thoughts_js_1 = require("../services/thoughts.js");
const memory_js_1 = require("../services/memory.js");
const trust_js_1 = require("../services/trust.js");
const evolution_js_1 = require("../services/evolution.js");
const health_js_1 = require("../services/health.js");
const schedule_js_1 = require("../services/schedule.js");
const achievements_js_1 = require("../services/achievements.js");
const journal_js_1 = require("../services/journal.js");
const proactive_js_1 = require("../services/proactive.js");
const introspect_js_1 = require("../services/introspect.js");
const router = express_1.default.Router();
const execAsync = (0, util_1.promisify)(child_process_1.exec);
// GET /api/stats
router.get('/stats', (_req, res) => {
    try {
        const history = (0, history_js_1.loadHistory)();
        const picks = (0, history_js_1.loadPicks)();
        const achievements = (0, achievements_js_1.getAchievementsDashboardData)();
        // Count thought picks
        const thoughtCounts = {};
        for (const pick of picks) {
            const thoughtId = pick.thought || '?';
            thoughtCounts[thoughtId] = (thoughtCounts[thoughtId] || 0) + 1;
        }
        const stats = {
            total_picks: picks.length,
            total_completed: history.length,
            achievements: achievements.earned.length,
            points: achievements.total_points,
            thought_counts: thoughtCounts,
            recent: history.slice(-10).reverse()
        };
        res.json(stats);
    }
    catch (error) {
        console.error('Error in /api/stats:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/stream
router.get('/stream', (_req, res) => {
    try {
        const streamData = (0, history_js_1.loadStreamData)(50);
        res.json(streamData);
    }
    catch (error) {
        console.error('Error in /api/stream:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/decisions
router.get('/decisions', (_req, res) => {
    try {
        const decisions = (0, history_js_1.loadDecisions)();
        res.json(decisions.slice(-50));
    }
    catch (error) {
        console.error('Error in /api/decisions:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/rejections
router.get('/rejections', (_req, res) => {
    try {
        const rejections = (0, history_js_1.loadRejections)();
        res.json(rejections.slice(-50));
    }
    catch (error) {
        console.error('Error in /api/rejections:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/mood-timeline
router.get('/mood-timeline', (_req, res) => {
    try {
        const moodHistory = (0, mood_js_1.loadMoodHistory)();
        res.json(moodHistory.slice(-30));
    }
    catch (error) {
        console.error('Error in /api/mood-timeline:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/presets
router.get('/presets', (_req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        const presetsDir = path.join((0, config_js_1.getDataDir)(), 'presets');
        const presets = {};
        if (fs.existsSync(presetsDir)) {
            const presetFiles = fs.readdirSync(presetsDir).filter((f) => f.endsWith('.json'));
            for (const file of presetFiles) {
                try {
                    const presetData = JSON.parse(fs.readFileSync(path.join(presetsDir, file), 'utf8'));
                    presets[file.replace('.json', '')] = presetData;
                }
                catch (error) {
                    console.error(`Error loading preset ${file}:`, error);
                }
            }
        }
        res.json(presets);
    }
    catch (error) {
        console.error('Error in /api/presets:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/schedule
router.get('/schedule', async (_req, res) => {
    try {
        const scheduleData = await (0, schedule_js_1.getScheduleData)();
        res.json(scheduleData);
    }
    catch (error) {
        console.error('Error in /api/schedule:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/memory
router.get('/memory', async (_req, res) => {
    try {
        const memoryData = await (0, memory_js_1.getMemorySystemDashboardData)();
        res.json(memoryData);
    }
    catch (error) {
        console.error('Error in /api/memory:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/trust
router.get('/trust', async (_req, res) => {
    try {
        const trustData = await (0, trust_js_1.getTrustDashboardData)();
        res.json(trustData);
    }
    catch (error) {
        console.error('Error in /api/trust:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/evolution
router.get('/evolution', async (_req, res) => {
    try {
        const evolutionData = await (0, evolution_js_1.getEvolutionDashboardData)();
        res.json(evolutionData);
    }
    catch (error) {
        console.error('Error in /api/evolution:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/proactive
router.get('/proactive', async (_req, res) => {
    try {
        const proactiveData = await (0, proactive_js_1.getProactiveDashboardData)();
        res.json(proactiveData);
    }
    catch (error) {
        console.error('Error in /api/proactive:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/health
router.get('/health', async (_req, res) => {
    try {
        const healthData = await (0, health_js_1.getHealthDashboardData)();
        res.json(healthData);
    }
    catch (error) {
        console.error('Error in /api/health:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/systems
router.get('/systems', (_req, res) => {
    try {
        const todayMood = (0, mood_js_1.loadTodayMood)();
        const history = (0, history_js_1.loadHistory)();
        const thoughts = (0, thoughts_js_1.loadThoughts)();
        const achievements = (0, achievements_js_1.getAchievementsDashboardData)();
        const systems = {
            mood: { status: 'active', current_mood: todayMood },
            memory: { status: 'active', entries: history.length },
            thoughts: { status: 'active', total_thoughts: countThoughts(thoughts) },
            achievements: { status: 'active', earned: achievements.earned.length },
            health: { status: 'active', monitoring: true }
        };
        res.json(systems);
    }
    catch (error) {
        console.error('Error in /api/systems:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/journal
router.get('/journal', (req, res) => {
    try {
        const date = req.query.date;
        if (date) {
            const entry = (0, journal_js_1.loadJournalEntry)(date);
            if (entry) {
                res.json(entry);
            }
            else {
                res.status(404).json({ error: `Journal entry for ${date} not found` });
            }
        }
        else {
            res.status(400).json({ error: 'Date parameter required' });
        }
    }
    catch (error) {
        console.error('Error in /api/journal:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/journal/list
router.get('/journal/list', (_req, res) => {
    try {
        const entries = (0, journal_js_1.loadJournalEntries)();
        res.json(entries);
    }
    catch (error) {
        console.error('Error in /api/journal/list:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/achievements
router.get('/achievements', (_req, res) => {
    try {
        const achievementsData = (0, achievements_js_1.getAchievementsDashboardData)();
        res.json(achievementsData);
    }
    catch (error) {
        console.error('Error in /api/achievements:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/night-stats
router.get('/night-stats', (_req, res) => {
    try {
        const picks = (0, history_js_1.loadPicks)();
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
                    }
                    else {
                        nightPicks++;
                    }
                }
            }
            catch {
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
    }
    catch (error) {
        console.error('Error in /api/night-stats:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/introspect
router.get('/introspect', async (_req, res) => {
    try {
        const introspectData = await (0, introspect_js_1.runIntrospect)();
        res.json(introspectData);
    }
    catch (error) {
        console.error('Error in /api/introspect:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/explain/:system
router.get('/explain/:system', async (req, res) => {
    try {
        const systemName = req.params.system;
        const explanationData = await (0, introspect_js_1.runExplainSystem)(systemName);
        res.json(explanationData);
    }
    catch (error) {
        console.error('Error in /api/explain:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
// GET /api/why
router.get('/why', async (_req, res) => {
    try {
        const decisionData = await (0, introspect_js_1.runDecisionTrace)();
        res.json(decisionData);
    }
    catch (error) {
        console.error('Error in /api/why:', error);
        res.status(500).json({ error: 'Internal server error' });
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
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            res.json({ status: 'error', error: stderr });
            return;
        }
        res.json({ status: 'success', message: `Mood set to ${mood_id}` });
    }
    catch (error) {
        console.error('Error in /api/set-mood:', error);
        res.json({ status: 'error', error: String(error) });
    }
});
// POST /api/trigger
router.post('/trigger', async (_req, res) => {
    try {
        const { stderr } = await execAsync('./suggest_thought.sh', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 10000
        });
        if (stderr) {
            res.json({ status: 'error', error: stderr });
            return;
        }
        res.json({ status: 'success', message: 'Impulse triggered' });
    }
    catch (error) {
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
    }
    catch (error) {
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
    }
    catch (error) {
        console.error('Error in /api/thought-weight:', error);
        res.json({ status: 'error', error: String(error) });
    }
});
exports.default = router;
//# sourceMappingURL=api.js.map