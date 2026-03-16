#!/usr/bin/env python3
"""
Learning Extractor - Extracts insights from session transcripts
Stores learnings in SQLite for cross-session recall and self-learning synthesis.

Captures: insights, decisions, gotchas, tool failures, approach pivots, error patterns.
Includes: signal tracking, quality filtering, fuzzy dedup, skill detection.
Location: /Users/quartershots/Source/.claude/hooks/extract-learnings.py
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

CLAUDE_DIR = Path("/Users/quartershots/Source/.claude")
CACHE_DIR = CLAUDE_DIR / "cache"
DB_PATH = CACHE_DIR / "learnings.db"

# Signal weights for scoring
SIGNAL_WEIGHTS = {
    "extracted": 1,
    "reinforced": 2,
    "recalled": 2,
    "corrected": 3,
    "applied": 3,
}

# Fuzzy dedup threshold (0.7 = 70% similar)
DEDUP_THRESHOLD = 0.7

# --- Extraction Patterns ---

# Explicit insight markers (Claude's own insight blocks, notes, etc.)
LEARNING_PATTERNS = [
    r"(?:I |i |we |We )?(?:learned|discovered|found out|realized|noticed) that ([^.!?\n]+[.!?])",
    r"(?:Note|NOTE|note)[:\s]+([^.!?\n]+[.!?])",
    r"(?:GOTCHA|Gotcha|gotcha)[:\s]+([^.!?\n]+[.!?])",
    r"(?:TIP|Tip|tip)[:\s]+([^.!?\n]+[.!?])",
    r"(?:Remember|REMEMBER)[:\s]+([^.!?\n]+[.!?])",
    r"(?:The key (?:insight|discovery|finding) (?:is|here|was))[:\s]+([^.!?\n]+[.!?])",
    r"(?:This means|This indicates|This suggests) ([^.!?\n]+[.!?])",
    r"(?:Turns out|It turns out) ([^.!?\n]+[.!?])",
    # Insight blocks (★ Insight format from explanatory style)
    r"★ Insight[─\s]*\n\*\*([^*]+)\*\*",
    r"\*\*Key (?:insight|discovery|finding):\*\*\s*([^\n]+)",
    r"\*\*Root cause[^:]*:\*\*\s*([^\n]+)",
]

DECISION_PATTERNS = [
    r"(?:decided to|choosing to|will use|going with|opted for|chose) ([^.!?\n]+[.!?])",
    r"(?:The approach|Our approach|approach is|best approach)[:\s]+([^.!?\n]+[.!?])",
    r"(?:strategy|Strategy|recommendation)[:\s]+([^.!?\n]+[.!?])",
    r"(?:Using|switching to|migrating to) ([^.!?\n]+?) (?:instead|because|since|for)",
]

GOTCHA_PATTERNS = [
    r"(?:careful|watch out|beware|avoid|warning)[:\s]+([^.!?\n]+[.!?])",
    r"(?:This caused|This broke|This failed because|The (?:issue|problem|bug) (?:is|was)) ([^.!?\n]+[.!?])",
    r"(?:doesn't work|won't work|can't be used) (?:because|since|when) ([^.!?\n]+[.!?])",
]

# Tool and workflow patterns (new for self-learning)
TOOL_FAILURE_PATTERNS = [
    r"(?:WebFetch|Bash|Read|Edit|Write|Glob|Grep) (?:failed|error|timeout|blocked)[^.!?\n]*([.!?])",
    r"(?:Request failed|command failed|Error:|error:)[:\s]*([^.!?\n]+[.!?])",
    r"(?:permission denied|access denied|403|404|timeout)[:\s]*([^.!?\n]+[.!?])",
]

APPROACH_PIVOT_PATTERNS = [
    r"(?:Let me try|Let me use|Instead,? (?:let me|I'll)|alternative approach)[:\s]*([^.!?\n]+[.!?]?)",
    r"(?:That didn't work|previous approach failed)[,.\s]+([^.!?\n]+[.!?]?)",
]


def init_db():
    """Initialize SQLite database with schema including signal tracking."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_path, content)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ralph_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path TEXT NOT NULL,
            prompt_hash TEXT,
            iterations INTEGER,
            outcome TEXT,
            lessons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            project_path TEXT NOT NULL,
            total_messages INTEGER DEFAULT 0,
            assistant_messages INTEGER DEFAULT 0,
            tool_calls INTEGER DEFAULT 0,
            tool_errors INTEGER DEFAULT 0,
            duration_estimate TEXT,
            topics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tool_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            tool_name TEXT NOT NULL,
            error_type TEXT,
            error_message TEXT,
            project_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Signal tracking (append-only event stream)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learning_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_id INTEGER NOT NULL,
            signal_type TEXT NOT NULL,
            session_id TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learning_id) REFERENCES learnings(id)
        )
    """)

    # Backport audit trail
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backport_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learning_id INTEGER NOT NULL,
            target_file TEXT NOT NULL,
            content_added TEXT NOT NULL,
            score_at_backport REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (learning_id) REFERENCES learnings(id)
        )
    """)

    # Add new columns to learnings (safe ALTER TABLE — SQLite ignores if exists)
    for col_sql in [
        "ALTER TABLE learnings ADD COLUMN primary_skill TEXT DEFAULT NULL",
        "ALTER TABLE learnings ADD COLUMN tags TEXT DEFAULT NULL",
        "ALTER TABLE learnings ADD COLUMN quality_score REAL DEFAULT 0",
        "ALTER TABLE learnings ADD COLUMN backported INTEGER DEFAULT 0",
    ]:
        try:
            conn.execute(col_sql)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_learnings_project ON learnings(project_path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_learnings_created ON learnings(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_failures_tool ON tool_failures(tool_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_learning ON learning_signals(learning_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_type ON learning_signals(signal_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_learnings_score ON learnings(quality_score)")

    conn.commit()
    return conn


# --- Skill Detection ---

_known_skills_cache = None


def get_known_skills():
    """Scan .claude/skills/ and .claude/commands/ for known skill names."""
    global _known_skills_cache
    if _known_skills_cache is not None:
        return _known_skills_cache

    skills = set()
    for search_dir in [CLAUDE_DIR / "skills", CLAUDE_DIR / "commands"]:
        if search_dir.exists():
            for f in search_dir.rglob("*.md"):
                # Extract skill name from filename or parent dir
                name = f.stem.lower()
                if name == "skill":
                    name = f.parent.name.lower()
                skills.add(name)
    _known_skills_cache = skills
    return skills


def detect_skill(content, transcript_text=""):
    """Detect which skill a learning is most related to."""
    known = get_known_skills()
    content_lower = content.lower()

    # Direct mention of a known skill name in the learning content
    for skill in known:
        if skill in content_lower:
            return skill

    # Check transcript context for skill invocation markers
    if transcript_text:
        for skill in known:
            # <command-name>skill-name</command-name> pattern
            if f"<command-name>{skill}</command-name>" in transcript_text:
                return skill

    return None


# --- Quality Filtering ---

def passes_quality_gate(content):
    """Check if a learning passes minimum quality requirements."""
    # Min length: filter fragments
    if len(content) <= 30:
        return False
    # Max length: already enforced upstream at 500
    if len(content) > 500:
        return False
    # Not a question
    if content.rstrip().endswith("?"):
        return False
    # Not pure code: skip if >60% is backtick/code content
    backtick_chars = content.count("`")
    if len(content) > 0 and backtick_chars / len(content) > 0.6:
        return False
    return True


# --- Fuzzy Dedup ---

def find_fuzzy_match(conn, content, category, project_path):
    """Find existing learning that fuzzy-matches this content. Returns (id, content) or None."""
    cursor = conn.execute(
        "SELECT id, content FROM learnings WHERE category = ? AND project_path = ?",
        (category, project_path),
    )
    for row in cursor.fetchall():
        existing_id, existing_content = row
        ratio = SequenceMatcher(None, content.lower(), existing_content.lower()).ratio()
        if ratio > DEDUP_THRESHOLD:
            return existing_id, existing_content
    return None


# --- Signal Emission ---

def emit_signal(conn, learning_id, signal_type, session_id=None, context=None):
    """Emit a signal for a learning (append-only event)."""
    ctx_json = json.dumps(context) if context else None
    try:
        conn.execute(
            "INSERT INTO learning_signals (learning_id, signal_type, session_id, context) VALUES (?, ?, ?, ?)",
            (learning_id, signal_type, session_id, ctx_json),
        )
    except sqlite3.Error:
        pass


def extract_patterns(text, patterns):
    """Extract matches from text using pattern list."""
    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            content = match.group(1).strip()
            # Clean up markdown formatting
            content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
            content = re.sub(r"`([^`]+)`", r"\1", content)
            if 20 < len(content) < 500:
                results.append(content)
    return results


def extract_tool_failures(text):
    """Extract tool failure patterns from assistant text."""
    failures = []

    tool_error_patterns = [
        (r"WebFetch.*?(?:failed|error|403|blocked|timeout)", "WebFetch"),
        (r"Bash.*?(?:Error|failed|exit code [1-9])", "Bash"),
        (r"(?:Read|Edit|Write).*?(?:does not exist|permission|error)", "FileOps"),
        (r"Glob.*?(?:no (?:matches|results)|empty)", "Glob"),
        (r"(?:command not found|No such file)", "Bash"),
        (r"rate.?limit|429|too many requests", "RateLimit"),
    ]

    for pattern, tool in tool_error_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(f"(.{{0,80}}{pattern}.{{0,80}})", text, re.IGNORECASE)
            msg = match.group(0).strip() if match else pattern
            failures.append((tool, msg[:200]))

    return failures


def extract_all(text):
    """Extract all learning types from text."""
    results = []

    for content in extract_patterns(text, LEARNING_PATTERNS):
        results.append(("learning", content))

    for content in extract_patterns(text, DECISION_PATTERNS):
        results.append(("decision", content))

    for content in extract_patterns(text, GOTCHA_PATTERNS):
        results.append(("gotcha", content))

    for content in extract_patterns(text, TOOL_FAILURE_PATTERNS):
        results.append(("tool_error", content))

    for content in extract_patterns(text, APPROACH_PIVOT_PATTERNS):
        results.append(("pivot", content))

    return results


def process_transcript(transcript_path):
    """Process transcript and store learnings + tool stats with signal tracking."""
    if not os.path.exists(transcript_path):
        return 0

    conn = init_db()
    project_path = os.getcwd()
    session_id = Path(transcript_path).stem
    stored = 0

    # Session-level counters
    total_msgs = 0
    assistant_msgs = 0
    tool_calls = 0
    tool_errors = 0

    # Collect full transcript text for skill detection
    full_transcript_text = ""

    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_type = entry.get("type", "")
                    total_msgs += 1

                    if entry_type != "assistant":
                        if entry_type == "progress":
                            tool_name = entry.get("tool_name", "")
                            if tool_name:
                                tool_calls += 1
                                if entry.get("error") or entry.get("is_error"):
                                    tool_errors += 1
                                    try:
                                        err_msg = str(entry.get("error", ""))[:200]
                                        conn.execute(
                                            "INSERT INTO tool_failures (session_id, tool_name, error_type, error_message, project_path) VALUES (?, ?, ?, ?, ?)",
                                            (session_id, tool_name, "tool_error", err_msg, project_path),
                                        )
                                    except sqlite3.Error:
                                        pass
                        continue

                    assistant_msgs += 1
                    message = entry.get("message", {})
                    content_blocks = message.get("content", [])

                    for block in content_blocks:
                        if not isinstance(block, dict):
                            continue

                        if block.get("type") == "text":
                            text = block.get("text", "")
                            full_transcript_text += text + "\n"

                            # Extract learnings
                            learnings = extract_all(text)
                            for category, learning_content in learnings:
                                # Quality gate
                                if not passes_quality_gate(learning_content):
                                    continue

                                # Fuzzy dedup check
                                match = find_fuzzy_match(conn, learning_content, category, project_path)
                                if match:
                                    # Existing learning found — emit reinforced signal
                                    existing_id, _ = match
                                    emit_signal(conn, existing_id, "reinforced", session_id,
                                                {"new_content": learning_content[:100]})
                                    continue

                                # New learning — insert
                                try:
                                    skill = detect_skill(learning_content, full_transcript_text)
                                    cursor = conn.execute(
                                        "INSERT OR IGNORE INTO learnings (project_path, category, content, source, primary_skill) VALUES (?, ?, ?, ?, ?)",
                                        (project_path, category, learning_content, "transcript", skill),
                                    )
                                    if cursor.rowcount > 0:
                                        learning_id = cursor.lastrowid
                                        emit_signal(conn, learning_id, "extracted", session_id)
                                        stored += 1
                                except sqlite3.Error:
                                    pass

                            # Extract tool failures from text
                            failures = extract_tool_failures(text)
                            for tool_name, err_msg in failures:
                                try:
                                    conn.execute(
                                        "INSERT INTO tool_failures (session_id, tool_name, error_type, error_message, project_path) VALUES (?, ?, ?, ?, ?)",
                                        (session_id, tool_name, "text_mentioned", err_msg, project_path),
                                    )
                                    tool_errors += 1
                                except sqlite3.Error:
                                    pass

                        elif block.get("type") == "tool_use":
                            tool_calls += 1

                except json.JSONDecodeError:
                    continue

        # Store session stats
        try:
            conn.execute(
                "INSERT OR IGNORE INTO session_stats (session_id, project_path, total_messages, assistant_messages, tool_calls, tool_errors) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, project_path, total_msgs, assistant_msgs, tool_calls, tool_errors),
            )
        except sqlite3.Error:
            pass

        conn.commit()

    except Exception as e:
        print(f"Error processing transcript: {e}", file=sys.stderr)

    finally:
        conn.close()

    return stored


def migrate_existing_learnings():
    """One-time migration: add signals for existing learnings, clean up fragments, fuzzy dedup."""
    conn = init_db()
    project_path = os.getcwd()

    # 1. Emit 'extracted' signal for all existing learnings that don't have one
    cursor = conn.execute("""
        SELECT l.id FROM learnings l
        LEFT JOIN learning_signals s ON l.id = s.learning_id AND s.signal_type = 'extracted'
        WHERE s.id IS NULL
    """)
    migrated = 0
    for (learning_id,) in cursor.fetchall():
        emit_signal(conn, learning_id, "extracted", session_id="migration")
        migrated += 1

    # 2. Delete low-quality learnings (content <= 30 chars)
    cursor = conn.execute("SELECT id, content FROM learnings WHERE length(content) <= 30")
    deleted = 0
    for (lid, content) in cursor.fetchall():
        conn.execute("DELETE FROM learning_signals WHERE learning_id = ?", (lid,))
        conn.execute("DELETE FROM learnings WHERE id = ?", (lid,))
        deleted += 1

    # 3. Fuzzy dedup: find near-duplicate pairs, merge by keeping older, emitting reinforced
    cursor = conn.execute(
        "SELECT id, content, category, project_path FROM learnings ORDER BY id"
    )
    all_learnings = cursor.fetchall()
    seen = []  # (id, content, category, project_path)
    deduped = 0

    for lid, content, category, pp in all_learnings:
        found_dup = False
        for sid, scontent, scat, spp in seen:
            if category == scat and pp == spp:
                ratio = SequenceMatcher(None, content.lower(), scontent.lower()).ratio()
                if ratio > DEDUP_THRESHOLD:
                    # Duplicate — emit reinforced on the older one, delete newer
                    ctx = {"merged_from": lid, "content": content[:100]}
                    emit_signal(conn, sid, "reinforced", "migration", ctx)
                    conn.execute("DELETE FROM learning_signals WHERE learning_id = ?", (lid,))
                    conn.execute("DELETE FROM learnings WHERE id = ?", (lid,))
                    deduped += 1
                    found_dup = True
                    break
        if not found_dup:
            seen.append((lid, content, category, pp))

    conn.commit()
    conn.close()

    print(f"Migration: {migrated} signals added, {deleted} fragments deleted, {deduped} duplicates merged", file=sys.stderr)
    return migrated, deleted, deduped


def record_ralph_run(iterations, outcome, lessons):
    """Record a Ralph loop run outcome."""
    conn = init_db()
    project_path = os.getcwd()
    try:
        conn.execute(
            "INSERT INTO ralph_runs (project_path, iterations, outcome, lessons) VALUES (?, ?, ?, ?)",
            (project_path, iterations, outcome, lessons),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    # Check for migration flag
    if "--migrate" in sys.argv:
        migrate_existing_learnings()
        sys.exit(0)

    # Read hook input from stdin (Claude Code passes session info as JSON)
    try:
        hook_input = json.loads(sys.stdin.read())
        transcript_path = hook_input.get("transcript_path", "")
    except (json.JSONDecodeError, Exception):
        transcript_path = sys.argv[1] if len(sys.argv) > 1 else ""

    if transcript_path:
        count = process_transcript(transcript_path)
        if count > 0:
            print(f"Extracted {count} learnings to database", file=sys.stderr)

    # Check if Ralph loop just ended
    ralph_state = Path(".claude/ralph-loop.local.md")
    if ralph_state.exists():
        try:
            content = ralph_state.read_text()
            iteration = re.search(r"iteration: (\d+)", content)
            if iteration:
                record_ralph_run(
                    iterations=int(iteration.group(1)),
                    outcome="session_end",
                    lessons="Session ended during Ralph loop",
                )
        except Exception:
            pass
