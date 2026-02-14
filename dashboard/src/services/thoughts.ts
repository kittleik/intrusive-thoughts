import fs from 'fs';
import { getFilePath } from './config.js';
import type { ThoughtsData, Thought } from '../types.js';

export function loadThoughts(): ThoughtsData {
  try {
    const thoughtsPath = getFilePath('thoughts.json');
    const data = fs.readFileSync(thoughtsPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading thoughts:', error);
    return { thoughts: {} };
  }
}

export function getThoughtById(thoughtId: string): Thought | null {
  const thoughtsData = loadThoughts();
  return thoughtsData.thoughts[thoughtId] || null;
}

export function getTopThoughts(pickCounts: Record<string, number>, limit = 10): Array<{
  id: string;
  mood: string;
  weight: number;
  prompt: string;
  times_picked: number;
}> {
  const thoughtsData = loadThoughts();
  const topThoughts: Array<{
    id: string;
    mood: string;
    weight: number;
    prompt: string;
    times_picked: number;
  }> = [];
  
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

export function calculateEffectiveWeights(moodId?: string): Record<string, number> {
  const thoughtsData = loadThoughts();
  const effectiveWeights: Record<string, number> = {};
  
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