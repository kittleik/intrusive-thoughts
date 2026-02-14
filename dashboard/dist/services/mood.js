"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadMoods = loadMoods;
exports.loadTodayMood = loadTodayMood;
exports.loadMoodHistory = loadMoodHistory;
exports.loadSoundtracks = loadSoundtracks;
exports.getCurrentMoodDisplay = getCurrentMoodDisplay;
const fs_1 = __importDefault(require("fs"));
const config_js_1 = require("./config.js");
function loadMoods() {
    try {
        const moodsPath = (0, config_js_1.getFilePath)('moods.json');
        const data = fs_1.default.readFileSync(moodsPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading moods:', error);
        return { base_moods: [] };
    }
}
function loadTodayMood() {
    try {
        const todayMoodPath = (0, config_js_1.getFilePath)('today_mood.json');
        const data = fs_1.default.readFileSync(todayMoodPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading today mood:', error);
        return null;
    }
}
function loadMoodHistory() {
    try {
        const moodHistoryPath = (0, config_js_1.getFilePath)('mood_history.json');
        const data = fs_1.default.readFileSync(moodHistoryPath, 'utf8');
        const parsed = JSON.parse(data);
        return parsed.history || [];
    }
    catch (error) {
        console.error('Error loading mood history:', error);
        return [];
    }
}
function loadSoundtracks() {
    try {
        const soundtracksPath = (0, config_js_1.getFilePath)('soundtracks.json');
        const data = fs_1.default.readFileSync(soundtracksPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading soundtracks:', error);
        return { mood_soundtracks: {} };
    }
}
function getCurrentMoodDisplay() {
    const todayMood = loadTodayMood();
    const soundtracks = loadSoundtracks();
    let mood_display = "🤔 Unknown";
    let mood_description = "";
    let today_soundtrack = "";
    if (todayMood) {
        const mood_id = todayMood.drifted_to || todayMood.id;
        const mood_emoji = todayMood.emoji;
        const mood_name = todayMood.name;
        mood_display = `${mood_emoji} ${mood_name}`;
        mood_description = todayMood.description || "";
        // Get soundtrack info
        const soundtrack_info = soundtracks.mood_soundtracks[mood_id];
        if (soundtrack_info) {
            const vibe = soundtrack_info.vibe_description || "";
            const genres = soundtrack_info.genres?.slice(0, 3).join(", ") || "";
            today_soundtrack = `${vibe} — ${genres}`;
        }
    }
    return { mood_display, mood_description, today_soundtrack };
}
//# sourceMappingURL=mood.js.map