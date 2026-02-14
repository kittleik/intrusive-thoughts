"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadEvolutionData = loadEvolutionData;
exports.getEvolutionSystemData = getEvolutionSystemData;
exports.getEvolutionDashboardData = getEvolutionDashboardData;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
function loadEvolutionData() {
    try {
        const evolutionDir = path_1.default.join((0, config_js_1.getDataDir)(), 'evolution');
        if (!fs_1.default.existsSync(evolutionDir)) {
            return { error: 'evolution directory not found' };
        }
        const evolutionData = {};
        const files = fs_1.default.readdirSync(evolutionDir);
        for (const file of files) {
            if (file.endsWith('.json')) {
                try {
                    const filePath = path_1.default.join(evolutionDir, file);
                    const data = JSON.parse(fs_1.default.readFileSync(filePath, 'utf8'));
                    const key = file.replace('.json', '');
                    evolutionData[key] = data;
                }
                catch (error) {
                    console.error(`Error loading evolution file ${file}:`, error);
                }
            }
        }
        return evolutionData;
    }
    catch (error) {
        console.error('Error loading evolution data:', error);
        return { error: 'evolution system unavailable' };
    }
}
async function getEvolutionSystemData() {
    try {
        // Try to call self_evolution.py dashboard function
        const { stdout, stderr } = await execAsync('python3 -c "from self_evolution import get_dashboard_data; import json; print(json.dumps(get_dashboard_data()))"', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            console.error('Evolution system stderr:', stderr);
        }
        return JSON.parse(stdout);
    }
    catch (error) {
        console.error('Error running evolution system:', error);
        // Fallback to loading evolution files directly
        return loadEvolutionData();
    }
}
async function getEvolutionDashboardData() {
    const systemData = await getEvolutionSystemData();
    if (systemData.error) {
        return loadEvolutionData();
    }
    return systemData;
}
//# sourceMappingURL=evolution.js.map