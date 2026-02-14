import express from 'express';
import path from 'path';
import { getDashboardPort, getDataDir } from './services/config.js';
import apiRouter from './routes/api.js';
import fs from 'fs';

const app = express();
const PORT = getDashboardPort();

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// CORS headers for local development
app.use((_req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With');
  
  if (_req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// Mount API routes
app.use('/api', apiRouter);

// Serve the main HTML file for root path
app.get('/', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Server error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Get version from VERSION file
function getVersion(): string {
  try {
    const versionPath = path.join(getDataDir(), 'VERSION');
    return fs.readFileSync(versionPath, 'utf8').trim();
  } catch {
    return 'TS-dev';
  }
}

// Graceful shutdown
let server: any;

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
    server.close((err: any) => {
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
  } else {
    process.exit(0);
  }
}

// Start server
const startServer = () => {
  try {
    server = app.listen(PORT, 'localhost', () => {
      const version = getVersion();
      console.log(`🧠 Starting Intrusive Thoughts Dashboard (TypeScript) v${version} on http://localhost:${PORT}`);
      console.log(`📁 Data directory: ${getDataDir()}`);
      console.log(`🔗 Open in browser: http://localhost:${PORT}`);
    });
    
    server.on('error', (err: any) => {
      if (err.code === 'EADDRINUSE') {
        console.error(`❌ Port ${PORT} is already in use. Please close the existing server or change the port.`);
      } else {
        console.error(`❌ Server error: ${err.message}`);
      }
      process.exit(1);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

export default app;