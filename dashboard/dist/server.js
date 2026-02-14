"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const path_1 = __importDefault(require("path"));
const config_js_1 = require("./services/config.js");
const api_js_1 = __importDefault(require("./routes/api.js"));
const fs_1 = __importDefault(require("fs"));
const app = (0, express_1.default)();
const PORT = (0, config_js_1.getDashboardPort)();
// Middleware
app.use(express_1.default.json());
app.use(express_1.default.urlencoded({ extended: true }));
// CORS headers for local development
app.use((_req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With');
    if (_req.method === 'OPTIONS') {
        res.sendStatus(200);
    }
    else {
        next();
    }
});
// Serve static files from public directory
app.use(express_1.default.static(path_1.default.join(__dirname, 'public')));
// Mount API routes
app.use('/api', api_js_1.default);
// Serve the main HTML file for root path
app.get('/', (_req, res) => {
    res.sendFile(path_1.default.join(__dirname, 'public', 'index.html'));
});
// 404 handler
app.use((_req, res) => {
    res.status(404).json({ error: 'Not found' });
});
// Error handler
app.use((err, _req, res, _next) => {
    console.error('Server error:', err);
    res.status(500).json({ error: 'Internal server error' });
});
// Get version from VERSION file
function getVersion() {
    try {
        const versionPath = path_1.default.join((0, config_js_1.getDataDir)(), 'VERSION');
        return fs_1.default.readFileSync(versionPath, 'utf8').trim();
    }
    catch {
        return 'TS-dev';
    }
}
// Graceful shutdown
let server;
process.on('SIGTERM', () => {
    console.log('\n🛑 SIGTERM received. Shutting down gracefully...');
    gracefulShutdown();
});
process.on('SIGINT', () => {
    console.log('\n🛑 SIGINT received. Shutting down gracefully...');
    gracefulShutdown();
});
function gracefulShutdown() {
    if (server) {
        server.close((err) => {
            if (err) {
                console.error('Error during server shutdown:', err);
                process.exit(1);
            }
            console.log('🛑 Server closed. Goodbye!');
            process.exit(0);
        });
        // Force close after 10 seconds
        setTimeout(() => {
            console.error('Could not close connections in time, forcefully shutting down');
            process.exit(1);
        }, 10000);
    }
    else {
        process.exit(0);
    }
}
// Start server
const startServer = () => {
    try {
        server = app.listen(PORT, '0.0.0.0', () => {
            const version = getVersion();
            console.log(`🧠 Starting Intrusive Thoughts Dashboard (TypeScript) v${version} on http://localhost:${PORT}`);
            console.log(`📁 Data directory: ${(0, config_js_1.getDataDir)()}`);
            console.log(`🔗 Open in browser: http://localhost:${PORT}`);
        });
        server.on('error', (err) => {
            if (err.code === 'EADDRINUSE') {
                console.error(`❌ Port ${PORT} is already in use. Please close the existing server or change the port.`);
            }
            else {
                console.error(`❌ Server error: ${err.message}`);
            }
            process.exit(1);
        });
    }
    catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
};
startServer();
exports.default = app;
//# sourceMappingURL=server.js.map