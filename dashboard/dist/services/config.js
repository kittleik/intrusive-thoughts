"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadConfig = loadConfig;
exports.getDataDir = getDataDir;
exports.getFilePath = getFilePath;
exports.get = get;
exports.getHumanName = getHumanName;
exports.getAgentName = getAgentName;
exports.getAgentEmoji = getAgentEmoji;
exports.getDashboardPort = getDashboardPort;
exports.isIntegrationEnabled = isIntegrationEnabled;
exports.getTimezone = getTimezone;
exports.getDataDirFromEnv = getDataDirFromEnv;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
let config = null;
function loadConfig() {
    if (config)
        return config;
    // Get base directory - go up one level from dashboard/ to intrusive-thoughts/
    const baseDir = path_1.default.resolve(__dirname, '../../../');
    const configFile = path_1.default.join(baseDir, 'config.json');
    const exampleConfigFile = path_1.default.join(baseDir, 'config.example.json');
    try {
        if (fs_1.default.existsSync(configFile)) {
            const configData = fs_1.default.readFileSync(configFile, 'utf8');
            config = JSON.parse(configData);
            return config;
        }
    }
    catch (error) {
        console.log(`Error loading config.json: ${error}`);
        console.log('Falling back to config.example.json');
    }
    try {
        if (fs_1.default.existsSync(exampleConfigFile)) {
            const configData = fs_1.default.readFileSync(exampleConfigFile, 'utf8');
            config = JSON.parse(configData);
            console.log('⚠️  Using config.example.json - copy to config.json and customize!');
            return config;
        }
    }
    catch (error) {
        console.log(`Error loading config.example.json: ${error}`);
    }
    // Last resort - minimal config
    console.log('⚠️  No config found! Using minimal defaults.');
    config = {
        human: { name: 'Human', timezone: 'UTC' },
        agent: { name: 'Agent', emoji: '🤖' },
        system: { data_dir: baseDir, dashboard_port: 3117 },
        integrations: {
            moltbook: { enabled: false },
            telegram: { enabled: false }
        }
    };
    return config;
}
function getDataDir() {
    const conf = loadConfig();
    // Expand ~ to home directory if needed
    let dataDir = conf.system.data_dir;
    if (dataDir.startsWith('~/')) {
        dataDir = path_1.default.join(process.env.HOME || '/', dataDir.slice(2));
    }
    return dataDir;
}
function getFilePath(filename) {
    return path_1.default.join(getDataDir(), filename);
}
function get(keyPath, defaultValue = null) {
    const conf = loadConfig();
    const keys = keyPath.split('.');
    let value = conf;
    try {
        for (const key of keys) {
            value = value[key];
        }
        return value;
    }
    catch {
        return defaultValue;
    }
}
function getHumanName() {
    return get('human.name', 'Human');
}
function getAgentName() {
    return get('agent.name', 'Agent');
}
function getAgentEmoji() {
    return get('agent.emoji', '🤖');
}
function getDashboardPort() {
    const port = process.env.PORT || get('system.dashboard_port', 3117);
    return typeof port === 'string' ? parseInt(port, 10) : port;
}
function isIntegrationEnabled(integration) {
    return get(`integrations.${integration}.enabled`, false);
}
function getTimezone() {
    return get('human.timezone', 'UTC');
}
// Environment variable override for DATA_DIR as mentioned in the requirements
function getDataDirFromEnv() {
    return process.env.DATA_DIR || getDataDir();
}
//# sourceMappingURL=config.js.map