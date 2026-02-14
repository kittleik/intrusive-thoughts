"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadHealthStatusData = loadHealthStatusData;
exports.loadHeartbeatData = loadHeartbeatData;
exports.getHealthMonitorData = getHealthMonitorData;
exports.getHealthDashboardData = getHealthDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
function loadHealthStatusData() {
    try {
        const healthDir = path_1.default.join((0, config_js_1.getDataDir)(), 'health');
        const statusPath = path_1.default.join(healthDir, 'status.json');
        if (!fs_1.default.existsSync(statusPath)) {
            return { error: 'health status file not found' };
        }
        const data = JSON.parse(fs_1.default.readFileSync(statusPath, 'utf8'));
        return data;
    }
    catch (error) {
        console.error('Error loading health status:', error);
        return { error: 'health status unavailable' };
    }
}
function loadHeartbeatData() {
    try {
        const healthDir = path_1.default.join((0, config_js_1.getDataDir)(), 'health');
        const heartbeatFiles = fs_1.default.readdirSync(healthDir).filter(f => f.startsWith('heartbeat') && f.endsWith('.json'));
        const heartbeats = [];
        for (const file of heartbeatFiles.sort().slice(-10)) { // Get last 10 heartbeat files
            try {
                const filePath = path_1.default.join(healthDir, file);
                const data = JSON.parse(fs_1.default.readFileSync(filePath, 'utf8'));
                heartbeats.push({ file, ...data });
            }
            catch (error) {
                console.error(`Error loading heartbeat file ${file}:`, error);
            }
        }
        return heartbeats;
    }
    catch (error) {
        console.error('Error loading heartbeat data:', error);
        return [];
    }
}
async function getHealthMonitorData() {
    try {
        // Try to call health_monitor.py dashboard function
        const { stdout, stderr } = await execAsync('python3 -c "from health_monitor import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            console.error('Health monitor stderr:', stderr);
        }
        return JSON.parse(stdout);
    }
    catch (error) {
        console.error('Error running health monitor:', error);
        // Fallback to loading health files directly
        const statusData = loadHealthStatusData();
        const heartbeats = loadHeartbeatData();
        return {
            status: statusData,
            heartbeats,
            error: statusData.error
        };
    }
}
async function getHealthDashboardData() {
    return await getHealthMonitorData();
}
//# sourceMappingURL=health.js.map