"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadHistory = loadHistory;
exports.loadPicks = loadPicks;
exports.loadRejections = loadRejections;
exports.loadDecisions = loadDecisions;
exports.loadStreamData = loadStreamData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const config_js_1 = require("./config.js");
const sessions_js_1 = require("./sessions.js");
/**
 * Load history from OpenClaw session logs, falling back to history.json
 */
function loadHistory() {
    // Try session logs first
    if ((0, sessions_js_1.hasSessionLogs)()) {
        try {
            const entries = (0, sessions_js_1.loadSessionHistory)();
            if (entries.length > 0)
                return entries;
        }
        catch (error) {
            console.error('Error loading session history, falling back to history.json:', error);
        }
    }
    // Fallback to history.json
    try {
        const historyPath = (0, config_js_1.getFilePath)('history.json');
        const data = fs_1.default.readFileSync(historyPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading history:', error);
        return [];
    }
}
function loadPicks() {
    try {
        const picksLogPath = path_1.default.join((0, config_js_1.getDataDir)(), 'data', 'log', 'picks.log');
        const lines = fs_1.default.readFileSync(picksLogPath, 'utf8').split('\n').filter(line => line.trim());
        const picks = [];
        for (const line of lines) {
            const parts = line.split(' | ');
            if (parts.length >= 1) {
                const timestamp = parts[0];
                const meta = { timestamp };
                // Parse metadata from remaining parts
                for (let i = 1; i < parts.length; i++) {
                    const part = parts[i];
                    if (part && part.includes('=')) {
                        const [key, value] = part.split('=', 2);
                        if (key && value !== undefined) {
                            meta[key] = value;
                        }
                    }
                }
                picks.push(meta);
            }
        }
        return picks;
    }
    catch (error) {
        console.error('Error loading picks:', error);
        return [];
    }
}
function loadRejections() {
    try {
        const rejectionsLogPath = path_1.default.join((0, config_js_1.getDataDir)(), 'data', 'log', 'rejections.log');
        const lines = fs_1.default.readFileSync(rejectionsLogPath, 'utf8').split('\n').filter(line => line.trim());
        const rejections = [];
        for (const line of lines) {
            const parts = line.split(' | ');
            if (parts.length >= 5) {
                rejections.push({
                    timestamp: parts[0] || '',
                    thought_id: parts[1] || '',
                    mood: parts[2] || '',
                    reason: parts[3] || '',
                    flavor_text: parts[4] || ''
                });
            }
        }
        return rejections;
    }
    catch (error) {
        console.error('Error loading rejections:', error);
        return [];
    }
}
function loadDecisions() {
    try {
        const decisionsPath = path_1.default.join((0, config_js_1.getDataDir)(), 'data', 'log', 'decisions.json');
        const data = fs_1.default.readFileSync(decisionsPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading decisions:', error);
        return [];
    }
}
function loadStreamData(limit = 50) {
    const streamItems = [];
    // Only use intrusive-thoughts own data (history.json), NOT OpenClaw session logs
    const history = loadHistory();
    for (const entry of history.slice(-limit)) {
        streamItems.push({
            type: entry.type || 'activity',
            timestamp: entry.timestamp || '',
            thought_id: entry.thought_id || 'unknown',
            mood: entry.mood || 'unknown',
            summary: entry.summary || `Completed ${entry.thought_id}`,
            details: entry
        });
    }
    // Add picks
    const picks = loadPicks();
    for (const pick of picks.slice(-limit)) {
        streamItems.push({
            type: 'pick',
            timestamp: pick.timestamp || '',
            thought_id: pick.thought || 'unknown',
            mood: pick.today_mood || 'unknown',
            summary: `Picked ${pick.thought || 'unknown'} thought`,
            details: pick
        });
    }
    // Add rejections
    const rejections = loadRejections();
    for (const rejection of rejections.slice(-limit)) {
        streamItems.push({
            type: 'rejection',
            timestamp: rejection.timestamp || '',
            thought_id: rejection.thought_id || 'unknown',
            mood: rejection.mood || 'unknown',
            summary: `Rejected ${rejection.thought_id || 'unknown'}: ${rejection.reason || 'no reason'}`,
            details: rejection
        });
    }
    // Add mood drifts from today_mood.json activity_log
    try {
        const todayMoodPath = (0, config_js_1.getFilePath)('today_mood.json');
        const todayMoodData = JSON.parse(fs_1.default.readFileSync(todayMoodPath, 'utf8'));
        if (todayMoodData && todayMoodData.activity_log) {
            for (const activity of todayMoodData.activity_log.slice(-limit)) {
                streamItems.push({
                    type: 'mood_drift',
                    timestamp: activity.time || '',
                    mood: activity.action?.to || 'unknown',
                    summary: `Mood drift: ${activity.action?.from || '?'} → ${activity.action?.to || '?'}`,
                    details: activity
                });
            }
        }
    }
    catch (error) {
        console.error('Error loading mood drift data:', error);
    }
    // Sort by timestamp (most recent first)
    streamItems.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
    return streamItems.slice(0, limit);
}
//# sourceMappingURL=history.js.map