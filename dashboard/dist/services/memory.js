"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadMemoryData = loadMemoryData;
exports.getMemorySystemDashboardData = getMemorySystemDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const config_js_1 = require("./config.js");
function loadMemoryData() {
    try {
        const memoryStoreDir = path_1.default.join((0, config_js_1.getDataDir)(), 'memory_store');
        const memoryFiles = ['episodic.json', 'semantic.json', 'procedural.json', 'working.json'];
        const memoryData = {};
        let totalEntries = 0;
        for (const filename of memoryFiles) {
            const filePath = path_1.default.join(memoryStoreDir, filename);
            try {
                if (fs_1.default.existsSync(filePath)) {
                    const data = JSON.parse(fs_1.default.readFileSync(filePath, 'utf8'));
                    const memoryType = filename.replace('.json', '');
                    memoryData[memoryType] = data;
                    // Count entries for health score
                    if (Array.isArray(data)) {
                        totalEntries += data.length;
                    }
                    else if (typeof data === 'object' && data !== null) {
                        totalEntries += Object.keys(data).length;
                    }
                }
            }
            catch (error) {
                console.error(`Error loading ${filename}:`, error);
                memoryData[filename.replace('.json', '')] = null;
            }
        }
        memoryData.total_entries = totalEntries;
        memoryData.recent_activity = getRecentMemoryActivity(memoryStoreDir);
        return memoryData;
    }
    catch (error) {
        console.error('Error loading memory data:', error);
        return { error: 'memory system unavailable' };
    }
}
function getRecentMemoryActivity(memoryStoreDir) {
    try {
        // Check file modification times to determine recent activity
        const files = fs_1.default.readdirSync(memoryStoreDir);
        let mostRecentFile = '';
        let mostRecentTime = 0;
        for (const file of files) {
            if (file.endsWith('.json')) {
                const filePath = path_1.default.join(memoryStoreDir, file);
                const stats = fs_1.default.statSync(filePath);
                if (stats.mtime.getTime() > mostRecentTime) {
                    mostRecentTime = stats.mtime.getTime();
                    mostRecentFile = file;
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
// Interface with memory system via subprocess if needed
async function getMemorySystemDashboardData() {
    // Try to import and call memory system's dashboard function
    try {
        // This would require running a subprocess to call memory_system.py
        // For now, return the JSON file data
        return loadMemoryData();
    }
    catch (error) {
        console.error('Error getting memory system dashboard data:', error);
        return { error: 'memory system unavailable' };
    }
}
//# sourceMappingURL=memory.js.map