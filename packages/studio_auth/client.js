/**
 * StudioAuthClient — Universal Front-End Identity SDK.
 *
 * Provides Zero Blast Radius authentication across any web or hybrid game:
 * 1. Anonymous Local Guest Sessions (localStorage + crypto-random ID)
 * 2. Google OpenID Connect (OIDC) with Pairwise Subject Identifiers (PPID) via Backend
 * 3. Studio Dedicated Account login via Backend
 *
 * When operating standalone without an active backend endpoint (apiBaseUrl),
 * the SDK enforces honest Local/Guest mode and prohibits fake local simulations.
 */

class StudioAuthClient {
  constructor(config = {}) {
    this.projectSlug = config.projectSlug || "default_app";
    this.apiBaseUrl = (config.apiBaseUrl || "").replace(/\/+$/, "");
    this.storageKey = `studio_auth_session_${this.projectSlug}`;
    this.onAuthChange = config.onAuthChange || null;
    this.currentSession = this.loadSession();
  }

  _generateSecureHex(bytes = 8) {
    if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
      const arr = new Uint8Array(bytes);
      crypto.getRandomValues(arr);
      return Array.from(arr, b => b.toString(16).padStart(2, "0")).join("");
    }
    return Date.now().toString(16);
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
    const rawId = this._generateSecureHex(6);
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

  async loginWithGoogle(credential) {
    if (!this.apiBaseUrl) {
      throw new Error("Autenticação Google OIDC requer apiBaseUrl ativo para verificação criptográfica no servidor.");
    }
    if (!credential) {
      throw new Error("Token ou credencial Google OIDC em falta.");
    }
    const response = await fetch(`${this.apiBaseUrl}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: credential, projectSlug: this.projectSlug }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.mensagem || "Falha na validação da sessão Google junto do servidor.");
    }
    const session = await response.json();
    this.saveSession(session);
    return session;
  }

  async loginWithDedicated(username, password) {
    if (!this.apiBaseUrl) {
      throw new Error("Autenticação Conta Dedicada requer apiBaseUrl ativo para validação PBKDF2 no servidor.");
    }
    if (!username || !password) {
      throw new Error("Nome de utilizador e palavra-passe são obrigatórios.");
    }
    const response = await fetch(`${this.apiBaseUrl}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username.trim(), password, projectSlug: this.projectSlug }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.mensagem || "Credenciais inválidas ou erro no servidor de autenticação.");
    }
    const session = await response.json();
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
