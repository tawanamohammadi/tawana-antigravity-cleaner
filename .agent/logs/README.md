# Agent Logs Directory

This directory contains detailed operational logs for debugging and development purposes.

## Log Files

### `browser-helper-operations.log`
Detailed logs of all browser cleaning, session management, and network optimization operations.

**Format:**
```
[TIMESTAMP] [LEVEL] Message
```

**Levels:**
- `DEBUG`: Technical details (file paths, SQL queries, cookie names)
- `INFO`: User-facing operations (started cleaning, found X items)
- `WARNING`: Potential issues (browser running, backup failed)
- `ERROR`: Operation failures (permission denied, database locked)

### Log Rotation
Logs are rotated when they exceed 10MB. Old logs are kept with `.1`, `.2` suffixes.

## Privacy Notice
These logs may contain sensitive information (file paths, cookie names). They are stored locally and never transmitted.

---

**Note for Developers:**
Use these logs to debug issues reported by users. The main user-facing log is still at `~/Desktop/Antigravity-Cleaner.log`.
