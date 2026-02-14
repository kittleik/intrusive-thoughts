"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadTrustStoreData = loadTrustStoreData;
exports.getTrustSystemStats = getTrustSystemStats;
exports.getTrustDashboardData = getTrustDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
function loadTrustStoreData() {
    try {
        const trustStoreDir = path_1.default.join((0, config_js_1.getDataDir)(), 'trust_store');
        if (!fs_1.default.existsSync(trustStoreDir)) {
            return { error: 'trust store directory not found' };
        }
        const trustData = {};
        const files = fs_1.default.readdirSync(trustStoreDir);
        for (const file of files) {
            if (file.endsWith('.json')) {
                try {
                    const filePath = path_1.default.join(trustStoreDir, file);
                    const data = JSON.parse(fs_1.default.readFileSync(filePath, 'utf8'));
                    const key = file.replace('.json', '');
                    trustData[key] = data;
                }
                catch (error) {
                    console.error(`Error loading trust file ${file}:`, error);
                }
            }
        }
        return trustData;
    }
    catch (error) {
        console.error('Error loading trust store data:', error);
        return { error: 'trust system unavailable' };
    }
}
async function getTrustSystemStats() {
    try {
        // Try to run trust_system.py get_stats
        const { stdout, stderr } = await execAsync('python3 trust_system.py get_stats', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            console.error('Trust system stderr:', stderr);
        }
        // Try to parse JSON output
        try {
            return JSON.parse(stdout);
        }
        catch {
            // If not JSON, wrap in object
            return {
                trust_score: 'unknown',
                status: stdout.trim() || 'unknown',
                raw_output: stdout
            };
        }
    }
    catch (error) {
        console.error('Error running trust system:', error);
        // Fallback to loading trust store files directly
        return loadTrustStoreData();
    }
}
async function getTrustDashboardData() {
    // Try to get stats via subprocess first, then fallback to direct file reading
    const stats = await getTrustSystemStats();
    if (stats.error) {
        return loadTrustStoreData();
    }
    return stats;
}
//# sourceMappingURL=trust.js.map