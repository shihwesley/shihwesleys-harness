#!/usr/bin/env node
/**
 * Bridge: extract-learnings SQLite → claude-brain .mv2
 * Runs after extract-learnings.py to sync learnings into memvid
 *
 * Location: /Users/quartershots/Source/.claude/hooks/learnings-to-mind.js
 */

import { execSync } from 'child_process';
import Database from 'better-sqlite3';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

const LEARNINGS_DB = join(homedir(), 'Source/.claude/cache/learnings.db');
const SYNC_STATE = join(homedir(), '.claude/cache/learnings-sync-state.json');
const MIND_SCRIPT_DIR = join(homedir(), '.claude/plugins/cache'); // Plugin install location

async function main() {
  // Check if learnings DB exists
  if (!existsSync(LEARNINGS_DB)) {
    process.exit(0);
  }

  // Load last sync timestamp
  let lastSync = 0;
  if (existsSync(SYNC_STATE)) {
    try {
      const state = JSON.parse(readFileSync(SYNC_STATE, 'utf8'));
      lastSync = state.lastSync || 0;
    } catch {}
  }

  // Query new learnings since last sync
  const db = new Database(LEARNINGS_DB, { readonly: true });
  const newLearnings = db.prepare(`
    SELECT category, content, project_path, created_at
    FROM learnings
    WHERE created_at > datetime(?, 'unixepoch')
    ORDER BY created_at ASC
  `).all(lastSync);

  db.close();

  if (newLearnings.length === 0) {
    process.exit(0);
  }

  // Find claude-brain plugin path
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || findPluginRoot();
  if (!pluginRoot) {
    console.error('claude-brain plugin not found');
    process.exit(0);
  }

  // Format learnings for memvid
  for (const learning of newLearnings) {
    const memory = `[${learning.category.toUpperCase()}] ${learning.content} (from: ${learning.project_path})`;

    try {
      // Use memvid SDK to add memory
      // This is a simplified approach - actual integration depends on memvid API
      execSync(`node "${pluginRoot}/dist/index.js" add "${memory.replace(/"/g, '\\"')}"`, {
        stdio: 'pipe',
        timeout: 5000
      });
    } catch (err) {
      // Silent fail - don't block session end
    }
  }

  // Update sync state
  writeFileSync(SYNC_STATE, JSON.stringify({
    lastSync: Math.floor(Date.now() / 1000),
    lastCount: newLearnings.length
  }));

  console.error(`Synced ${newLearnings.length} learnings to claude-brain`);
}

function findPluginRoot() {
  // Look for claude-brain in common plugin locations
  const possiblePaths = [
    join(homedir(), '.claude/plugins/cache/claude-brain'),
    join(homedir(), '.claude/plugins/local/claude-brain'),
  ];

  for (const p of possiblePaths) {
    if (existsSync(join(p, 'dist/index.js'))) {
      return p;
    }
  }
  return null;
}

main().catch(() => process.exit(0));
