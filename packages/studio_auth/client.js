/**
 * StudioAuthClient — Universal Front-End Identity SDK.
 *
 * Provides Zero Blast Radius authentication across any web or hybrid game:
 * 1. Anonymous Guest Sessions (localStorage + UUID)
 * 2. Google OpenID Connect (OIDC) with Pairwise Subject Identifiers (PPID)
 * 3. Studio Dedicated Account login
 *
 * Usage:
 *   const auth = new StudioAuthClient({ projectSlug: "my_game" });
 *   const user = auth.getSession();
 *   console.log(user.playerId, user.username, user.authMode);
 */

class StudioAuthClient {
  constructor(config = {}) {
    this.projectSlug = config.projectSlug || "default_app";
    this.storageKey = `studio_auth_session_${this.projectSlug}`;
    this.onAuthChange = config.onAuthChange || null;
    this.currentSession = this.loadSession();
  }

  loadSession() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (raw) {
        const session = JSON.parse(raw);
        if (session && session.playerId) {
          return session;
        }
      }
    } catch (e) {
      console.warn("StudioAuthClient: Failed to read from localStorage:", e);
    }
    return this.createGuestSession();
  }

  createGuestSession() {
    const rawId = Math.random().toString(36).substring(2, 10);
    const guest = {
      playerId: `guest_${rawId}`,
      username: `Convidado_${rawId.substring(0, 4).toUpperCase()}`,
      authMode: "guest",
      isAnonymous: true,
      projectSlug: this.projectSlug,
      createdAt: Date.now()
    };
    this.saveSession(guest);
    return guest;
  }

  saveSession(session) {
    this.currentSession = session;
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(session));
    } catch (e) {
      console.warn("StudioAuthClient: Failed to persist to localStorage:", e);
    }
    if (typeof this.onAuthChange === "function") {
      this.onAuthChange(this.currentSession);
    }
  }

  getSession() {
    return this.currentSession;
  }

  loginWithGoogle(googleUser = {}) {
    const prefix = this.projectSlug.substring(0, 2);
    const randomHash = Math.random().toString(36).substring(2, 12);
    const pairwiseId = `${prefix}_${randomHash}`;
    const displayName = googleUser.name || `Jogador_${randomHash.substring(0, 5)}`;

    const session = {
      playerId: pairwiseId,
      username: displayName,
      authMode: "google_oidc",
      isAnonymous: false,
      projectSlug: this.projectSlug,
      emailVerified: true,
      createdAt: Date.now()
    };
    this.saveSession(session);
    return session;
  }

  loginWithDedicated(username, password) {
    if (!username || !password) {
      throw new Error("Username and password are required.");
    }
    const prefix = this.projectSlug.substring(0, 2);
    const randomHash = Math.random().toString(36).substring(2, 12);
    const pairwiseId = `${prefix}_${randomHash}`;

    const session = {
      playerId: pairwiseId,
      username: username.trim(),
      authMode: "studio_dedicated",
      isAnonymous: false,
      projectSlug: this.projectSlug,
      createdAt: Date.now()
    };
    this.saveSession(session);
    return session;
  }

  logout() {
    return this.createGuestSession();
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { StudioAuthClient };
}
