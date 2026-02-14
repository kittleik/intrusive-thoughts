"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadThoughts = loadThoughts;
exports.getThoughtById = getThoughtById;
exports.getTopThoughts = getTopThoughts;
exports.calculateEffectiveWeights = calculateEffectiveWeights;
const fs_1 = __importDefault(require("fs"));
const config_js_1 = require("./config.js");
function loadThoughts() {
    try {
        const thoughtsPath = (0, config_js_1.getFilePath)('thoughts.json');
        const data = fs_1.default.readFileSync(thoughtsPath, 'utf8');
        return JSON.parse(data);
    }
    catch (error) {
        console.error('Error loading thoughts:', error);
        return { thoughts: {} };
    }
}
function getThoughtById(thoughtId) {
    const thoughtsData = loadThoughts();
    return thoughtsData.thoughts[thoughtId] || null;
}
function getTopThoughts(pickCounts, limit = 10) {
    const thoughtsData = loadThoughts();
    const topThoughts = [];
    // Sort picks by count and take top entries
    const sortedPicks = Object.entries(pickCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, limit);
    for (const [thoughtId, count] of sortedPicks) {
        const thoughtData = thoughtsData.thoughts[thoughtId];
        if (thoughtData) {
            const moodWeights = thoughtData.weights || {};
            const moodName = Object.keys(moodWeights).length > 0
                ? Object.keys(moodWeights).reduce((a, b) => (moodWeights[a] || 0) > (moodWeights[b] || 0) ? a : b)
                : "unknown";
            topThoughts.push({
                id: thoughtId,
                mood: moodName,
                weight: thoughtData.weight || 1,
                prompt: thoughtData.prompt || `Unknown thought ${thoughtId}`,
                times_picked: count,
            });
        }
    }
    return topThoughts;
}
function calculateEffectiveWeights(moodId) {
    const thoughtsData = loadThoughts();
    const effectiveWeights = {};
    for (const [thoughtId, thought] of Object.entries(thoughtsData.thoughts)) {
        let weight = thought.weight || 1;
        // Apply mood modifier if mood is specified
        if (moodId && thought.weights && thought.weights[moodId]) {
            weight *= thought.weights[moodId];
        }
        effectiveWeights[thoughtId] = weight;
    }
    return effectiveWeights;
}
//# sourceMappingURL=thoughts.js.map