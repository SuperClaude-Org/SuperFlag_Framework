interface SessionData {
  flags: Map<string, number>;
  lastUsed: number;
}

interface DuplicateInfo {
  detected: string[];
  counts: Record<string, number>;
}

export class SessionManager {
  private sessions: Map<string, SessionData>;
  private maxSessions: number = 100;
  private ttlSeconds: number = 3600; // 1 hour

  constructor() {
    this.sessions = new Map();
  }

  /**
   * Get current session ID based on process and thread-like context
   */
  private getCurrentSessionId(): string {
    // In Node.js, we use process.pid and a pseudo-thread identifier
    const processId = process.pid;
    const threadId = require('worker_threads').threadId || 0;
    return `mcp_${processId}_${threadId}`;
  }

  /**
   * Get or create a session
   */
  private getSession(sessionId?: string): SessionData {
    if (!sessionId) {
      sessionId = this.getCurrentSessionId();
    }

    const currentTime = Date.now();

    // Clean expired sessions
    for (const [sid, data] of this.sessions.entries()) {
      if (currentTime - data.lastUsed > this.ttlSeconds * 1000) {
        this.sessions.delete(sid);
      }
    }

    // Get or create session
    let session = this.sessions.get(sessionId);
    if (!session) {
      // Evict oldest if at capacity
      if (this.sessions.size >= this.maxSessions) {
        const oldestKey = this.sessions.keys().next().value;
        if (oldestKey) {
          this.sessions.delete(oldestKey);
        }
      }

      session = {
        flags: new Map(),
        lastUsed: currentTime,
      };
      this.sessions.set(sessionId, session);
    }

    // Update last used
    session.lastUsed = currentTime;
    return session;
  }

  /**
   * Check for duplicate flags in current session
   */
  checkDuplicateFlags(flags: string[]): DuplicateInfo | null {
    const session = this.getSession();
    const usedFlags = session.flags;

    const duplicates: string[] = [];
    const counts: Record<string, number> = {};

    for (const flag of flags) {
      if (usedFlags.has(flag)) {
        duplicates.push(flag);
        counts[flag] = usedFlags.get(flag) || 0;
      }
    }

    if (duplicates.length > 0) {
      return {
        detected: duplicates,
        counts: counts,
      };
    }

    return null;
  }

  /**
   * Update flags in current session
   */
  updateFlags(flags: string[]): void {
    const session = this.getSession();

    for (const flag of flags) {
      const currentCount = session.flags.get(flag) || 0;
      session.flags.set(flag, currentCount + 1);
    }
  }

  /**
   * Reset current session flags
   */
  resetCurrentSession(): void {
    const sessionId = this.getCurrentSessionId();
    const session = this.sessions.get(sessionId);

    if (session) {
      session.flags.clear();
      session.lastUsed = Date.now();
    }
  }

  /**
   * Clear all sessions (for testing or cleanup)
   */
  clearAllSessions(): void {
    this.sessions.clear();
  }

  /**
   * Get session statistics
   */
  getStats(): { sessionCount: number; totalFlags: number } {
    let totalFlags = 0;

    for (const session of this.sessions.values()) {
      for (const count of session.flags.values()) {
        totalFlags += count;
      }
    }

    return {
      sessionCount: this.sessions.size,
      totalFlags: totalFlags,
    };
  }
}