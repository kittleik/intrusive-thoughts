"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadJournalEntries = loadJournalEntries;
exports.loadJournalEntry = loadJournalEntry;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const config_js_1 = require("./config.js");
function loadJournalEntries(limit) {
    try {
        const journalDir = path_1.default.join((0, config_js_1.getDataDir)(), 'journal');
        if (!fs_1.default.existsSync(journalDir)) {
            return [];
        }
        const entries = [];
        const files = fs_1.default.readdirSync(journalDir).filter(f => f.endsWith('.md'));
        for (const file of files) {
            try {
                const filePath = path_1.default.join(journalDir, file);
                const content = fs_1.default.readFileSync(filePath, 'utf8');
                entries.push({
                    date: file.replace('.md', ''),
                    filename: file,
                    content,
                    preview: content.length > 300 ? content.substring(0, 300) + '...' : content,
                    word_count: content.split(/\s+/).length
                });
            }
            catch (error) {
                console.error(`Error loading journal file ${file}:`, error);
            }
        }
        // Sort by date (most recent first)
        entries.sort((a, b) => b.date.localeCompare(a.date));
        if (limit) {
            return entries.slice(0, limit);
        }
        return entries;
    }
    catch (error) {
        console.error('Error loading journal entries:', error);
        return [];
    }
}
function loadJournalEntry(date) {
    try {
        const journalDir = path_1.default.join((0, config_js_1.getDataDir)(), 'journal');
        const filePath = path_1.default.join(journalDir, `${date}.md`);
        if (!fs_1.default.existsSync(filePath)) {
            return null;
        }
        const content = fs_1.default.readFileSync(filePath, 'utf8');
        return {
            date,
            filename: `${date}.md`,
            content,
            preview: content.length > 300 ? content.substring(0, 300) + '...' : content,
            word_count: content.split(/\s+/).length
        };
    }
    catch (error) {
        console.error(`Error loading journal entry for ${date}:`, error);
        return null;
    }
}
//# sourceMappingURL=journal.js.map