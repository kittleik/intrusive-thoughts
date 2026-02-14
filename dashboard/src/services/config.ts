import fs from 'fs';
import path from 'path';

interface Config {
  human: {
    name: string;
    timezone: string;
    telegram_target?: string;
  };
  agent: {
    name: string;
    emoji: string;
  };
  system: {
    data_dir: string;
    dashboard_port: number;
  };
  integrations: {
    moltbook: { enabled: boolean };
    telegram: { enabled: boolean };
  };
}

let config: Config | null = null;

export function loadConfig(): Config {
  if (config) return config;

  // Get base directory - go up one level from dashboard/ to intrusive-thoughts/
  const baseDir = path.resolve(__dirname, '../../../');
  
  const configFile = path.join(baseDir, 'config.json');
  const exampleConfigFile = path.join(baseDir, 'config.example.json');
  
  try {
    if (fs.existsSync(configFile)) {
      const configData = fs.readFileSync(configFile, 'utf8');
      config = JSON.parse(configData);
      return config!;
    }
  } catch (error) {
    console.log(`Error loading config.json: ${error}`);
    console.log('Falling back to config.example.json');
  }
  
  try {
    if (fs.existsSync(exampleConfigFile)) {
      const configData = fs.readFileSync(exampleConfigFile, 'utf8');
      config = JSON.parse(configData);
      console.log('⚠️  Using config.example.json - copy to config.json and customize!');
      return config!;
    }
  } catch (error) {
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

export function getDataDir(): string {
  const conf = loadConfig();
  // Expand ~ to home directory if needed
  let dataDir = conf.system.data_dir;
  if (dataDir.startsWith('~/')) {
    dataDir = path.join(process.env.HOME || '/', dataDir.slice(2));
  }
  return dataDir;
}

export function getFilePath(filename: string): string {
  return path.join(getDataDir(), filename);
}

export function get(keyPath: string, defaultValue: any = null): any {
  const conf = loadConfig();
  const keys = keyPath.split('.');
  let value: any = conf;
  
  try {
    for (const key of keys) {
      value = value[key];
    }
    return value;
  } catch {
    return defaultValue;
  }
}

export function getHumanName(): string {
  return get('human.name', 'Human');
}

export function getAgentName(): string {
  return get('agent.name', 'Agent');
}

export function getAgentEmoji(): string {
  return get('agent.emoji', '🤖');
}

export function getDashboardPort(): number {
  const port = process.env.PORT || get('system.dashboard_port', 3117);
  return typeof port === 'string' ? parseInt(port, 10) : port;
}

export function isIntegrationEnabled(integration: string): boolean {
  return get(`integrations.${integration}.enabled`, false);
}

export function getTimezone(): string {
  return get('human.timezone', 'UTC');
}

// Environment variable override for DATA_DIR as mentioned in the requirements
export function getDataDirFromEnv(): string {
  return process.env.DATA_DIR || getDataDir();
}