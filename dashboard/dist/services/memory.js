"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadMemoryData = loadMemoryData;
exports.getMemorySystemDashboardData = getMemorySystemDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const os_1 = __importDefault(require("os"));
const config_js_1 = require("./config.js");
function loadMemoryData() {
    try {
        // Check OpenClaw's native memory system instead of old memory_store
        const openclawMemoryDir = path_1.default.join(os_1.default.homedir(), '.openclaw', 'workspace', 'memory');
        const memoryMdPath = path_1.default.join(os_1.default.homedir(), '.openclaw', 'workspace', 'MEMORY.md');
        const moodPatternsPath = path_1.default.join((0, config_js_1.getDataDir)(), 'mood_patterns.md');
        const memoryData = {};
        let totalEntries = 0;
        // Check OpenClaw MEMORY.md
        if (fs_1.default.existsSync(memoryMdPath)) {
            try {
                const content = fs_1.default.readFileSync(memoryMdPath, 'utf8');
                memoryData.long_term_memory = {
                    size: content.length,
                    last_updated: fs_1.default.statSync(memoryMdPath).mtime,
                    status: 'available'
                };
                totalEntries += 1;
            }
            catch (error) {
                memoryData.long_term_memory = { status: 'error', error: error.toString() };
            }
        }
        else {
            memoryData.long_term_memory = { status: 'missing' };
        }
        // Check daily memory files
        if (fs_1.default.existsSync(openclawMemoryDir)) {
            try {
                const files = fs_1.default.readdirSync(openclawMemoryDir);
                const dailyFiles = files.filter(f => f.match(/^\d{4}-\d{2}-\d{2}\.md$/));
                memoryData.daily_memories = {
                    count: dailyFiles.length,
                    files: dailyFiles.sort().reverse().slice(0, 10), // Most recent 10
                    status: 'available'
                };
                totalEntries += dailyFiles.length;
            }
            catch (error) {
                memoryData.daily_memories = { status: 'error', error: error.toString() };
            }
        }
        else {
            memoryData.daily_memories = { status: 'missing' };
        }
        // Check mood patterns markdown
        if (fs_1.default.existsSync(moodPatternsPath)) {
            try {
                const content = fs_1.default.readFileSync(moodPatternsPath, 'utf8');
                const moodEntries = (content.match(/^## \d{4}-\d{2}-\d{2}/gm) || []).length;
                memoryData.mood_patterns = {
                    entries: moodEntries,
                    last_updated: fs_1.default.statSync(moodPatternsPath).mtime,
                    status: 'available'
                };
                totalEntries += moodEntries;
            }
            catch (error) {
                memoryData.mood_patterns = { status: 'error', error: error.toString() };
            }
        }
        else {
            memoryData.mood_patterns = { status: 'missing' };
        }
        memoryData.total_entries = totalEntries;
        memoryData.recent_activity = getRecentMemoryActivity();
        return memoryData;
    }
    catch (error) {
        console.error('Error loading memory data:', error);
        return { error: 'memory system unavailable' };
    }
}
function getRecentMemoryActivity() {
    try {
        const openclawMemoryDir = path_1.default.join(os_1.default.homedir(), '.openclaw', 'workspace', 'memory');
        const memoryMdPath = path_1.default.join(os_1.default.homedir(), '.openclaw', 'workspace', 'MEMORY.md');
        let mostRecentTime = 0;
        let mostRecentFile = '';
        // Check MEMORY.md
        if (fs_1.default.existsSync(memoryMdPath)) {
            const stats = fs_1.default.statSync(memoryMdPath);
            if (stats.mtime.getTime() > mostRecentTime) {
                mostRecentTime = stats.mtime.getTime();
                mostRecentFile = 'MEMORY.md';
            }
        }
        // Check daily memory files
        if (fs_1.default.existsSync(openclawMemoryDir)) {
            const files = fs_1.default.readdirSync(openclawMemoryDir);
            for (const file of files) {
                if (file.endsWith('.md')) {
                    const filePath = path_1.default.join(openclawMemoryDir, file);
                    const stats = fs_1.default.statSync(filePath);
                    if (stats.mtime.getTime() > mostRecentTime) {
                        mostRecentTime = stats.mtime.getTime();
                        mostRecentFile = file;
                    }
                }
            }
        }
        if (mostRecentFile) {
            const timeDiff = Date.now() - mostRecentTime;
            const hoursAgo = Math.floor(timeDiff / (1000 * 60 * 60));
            return `${mostRecentFile} updated ${hoursAgo}h ago`;
        }
        return 'No recent activity';
    }
    catch (error) {
        return 'Unknown';
    }
}
// OpenClaw native memory interface
async function getMemorySystemDashboardData() {
    try {
        return loadMemoryData();
    }
    catch (error) {
        console.error('Error getting memory system dashboard data:', error);
        return { error: 'memory system unavailable' };
    }
}
//# sourceMappingURL=memory.js.map