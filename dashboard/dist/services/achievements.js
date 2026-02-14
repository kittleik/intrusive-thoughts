"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadAllAchievements = loadAllAchievements;
exports.loadEarnedAchievements = loadEarnedAchievements;
exports.getAchievementsDashboardData = getAchievementsDashboardData;
const fs_1 = __importDefault(require("fs"));
const config_js_1 = require("./config.js");
function loadAllAchievements() {
    try {
        const achievementsPath = (0, config_js_1.getFilePath)('achievements.json');
        const data = fs_1.default.readFileSync(achievementsPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading achievements:', error);
        return { achievements: {}, tiers: {} };
    }
}
function loadEarnedAchievements() {
    try {
        const earnedPath = (0, config_js_1.getFilePath)('achievements_earned.json');
        const data = fs_1.default.readFileSync(earnedPath, 'utf8');
        const parsed = JSON.parse(data);
        // Handle both old and new formats
        if (Array.isArray(parsed)) {
            // Old format - convert to new format
            return {
                earned: parsed,
                total_points: parsed.reduce((sum, achievement) => sum + (achievement.points || 0), 0)
            };
        }
        // New format
        return parsed;
    }
    catch (error) {
        console.error('Error loading earned achievements:', error);
        return { earned: [], total_points: 0 };
    }
}
function getAchievementsDashboardData() {
    const earned = loadEarnedAchievements();
    const allAchievements = loadAllAchievements();
    return {
        earned: earned.earned || [],
        total_points: earned.total_points || 0,
        all_achievements: allAchievements
    };
}
//# sourceMappingURL=achievements.js.map