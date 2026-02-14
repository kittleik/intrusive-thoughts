"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadWalData = loadWalData;
exports.getProactiveSystemData = getProactiveSystemData;
exports.getProactiveDashboardData = getProactiveDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
function loadWalData() {
    try {
        const walDir = path_1.default.join((0, config_js_1.getDataDir)(), 'wal');
        if (!fs_1.default.existsSync(walDir)) {
            return [];
        }
        const walEntries = [];
        const files = fs_1.default.readdirSync(walDir).filter(f => f.endsWith('.json'));
        // Sort files by name (should be chronological) and get recent ones
        for (const file of files.sort().slice(-20)) {
            try {
                const filePath = path_1.default.join(walDir, file);
                const data = JSON.parse(fs_1.default.readFileSync(filePath, 'utf8'));
                walEntries.push({ file, ...data });
            }
            catch (error) {
                console.error(`Error loading wal file ${file}:`, error);
            }
        }
        return walEntries;
    }
    catch (error) {
        console.error('Error loading wal data:', error);
        return [];
    }
}
async function getProactiveSystemData() {
    try {
        // Try to call proactive.py dashboard function
        const { stdout, stderr } = await execAsync('python3 -c "from proactive import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            console.error('Proactive system stderr:', stderr);
        }
        return JSON.parse(stdout);
    }
    catch (error) {
        console.error('Error running proactive system:', error);
        // Fallback to loading wal files directly
        const walData = loadWalData();
        return {
            wal_entries: walData,
            total_entries: walData.length,
            recent_activity: walData.length > 0 ? `${walData.length} entries` : 'No recent activity'
        };
    }
}
async function getProactiveDashboardData() {
    const systemData = await getProactiveSystemData();
    if (systemData.error) {
        const walData = loadWalData();
        return {
            wal_entries: walData,
            total_entries: walData.length,
            recent_activity: walData.length > 0 ? `${walData.length} entries` : 'No recent activity',
            error: 'proactive system unavailable'
        };
    }
    return systemData;
}
//# sourceMappingURL=proactive.js.map