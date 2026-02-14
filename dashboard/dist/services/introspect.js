"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runIntrospect = runIntrospect;
exports.runExplainSystem = runExplainSystem;
exports.runDecisionTrace = runDecisionTrace;
const child_process_1 = require("child_process");
const util_1 = require("util");
const config_js_1 = require("./config.js");
const execAsync = (0, util_1.promisify)(child_process_1.exec);
async function runIntrospect() {
    try {
        const { stdout, stderr } = await execAsync('python3 introspect.py', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 10000
        });
        if (stderr) {
            console.error('Introspect stderr:', stderr);
        }
        return JSON.parse(stdout);
    }
    catch (error) {
        console.error('Error running introspect:', error);
        return { error: `Failed to run introspect: ${error}` };
    }
}
async function runExplainSystem(systemName) {
    try {
        const { stdout, stderr } = await execAsync(`python3 explain_system.py ${systemName}`, {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 10000
        });
        if (stderr) {
            return {
                error: `System '${systemName}' not found or error occurred`,
                stderr: stderr
            };
        }
        return {
            output: stdout,
            system: systemName
        };
    }
    catch (error) {
        console.error(`Error explaining ${systemName}:`, error);
        return { error: `Failed to explain ${systemName}: ${error}` };
    }
}
async function runDecisionTrace() {
    try {
        const { stdout, stderr } = await execAsync('python3 decision_trace.py', {
            cwd: (0, config_js_1.getDataDir)(),
            timeout: 10000
        });
        if (stderr) {
            return {
                error: 'No recent decisions found',
                stderr: stderr
            };
        }
        return {
            output: stdout
        };
    }
    catch (error) {
        console.error('Error tracing decision:', error);
        return { error: `Failed to trace decision: ${error}` };
    }
}
//# sourceMappingURL=introspect.js.map