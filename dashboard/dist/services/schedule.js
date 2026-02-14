"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getScheduleData = getScheduleData;
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const fs_1 = __importDefault(require("fs"));
const execAsync = (0, util_1.promisify)(child_process_1.exec);
async function getScheduleData() {
    try {
        // Run schedule_day.py --json to get schedule data
        const { stdout, stderr } = await execAsync('python3 schedule_day.py --json', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 5000
        });
        if (stderr) {
            console.error('Schedule system stderr:', stderr);
        }
        const data = JSON.parse(stdout);
        return data;
    }
    catch (error) {
        console.error('Error running schedule system:', error);
        // Fallback - try to load today_schedule.json if it exists
        try {
            const todaySchedulePath = (0, config_js_1.getFilePath)('today_schedule.json');
            const data = JSON.parse(fs_1.default.readFileSync(todaySchedulePath, 'utf8'));
            return {
                schedule: data.schedule || [],
                current_phase: data.current_phase || 'unknown'
            };
        }
        catch (fallbackError) {
            console.error('Error loading today_schedule.json:', fallbackError);
            return {
                schedule: [],
                current_phase: 'unknown'
            };
        }
    }
}
//# sourceMappingURL=schedule.js.map