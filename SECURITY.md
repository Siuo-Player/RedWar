# Security & Data Protection Policy

## 1. Reporting a Vulnerability

Please report security vulnerabilities privately to the repository owner rather than opening a public issue with undisclosed details.

When reporting, include:
- Affected component and file/path when known;
- A concise description of the vulnerability;
- Reproduction steps or a minimal proof of concept when safe to provide;
- Impact assessment, if known.

Do not include passwords, API keys, access tokens, private keys, or other credentials in a report.

---

## 2. Information & Data Security Principles

RedWar is committed to privacy by design and zero unnecessary data retention:

### 2.1 Data Minimization & Privacy
- **No Sensitive PII**: RedWar does not store personal emails, real names, passwords, or payment credentials.
- **Player Identity**: Leaderboards and match histories store only chosen player handles and ELO ratings.
- **Session Tokens**: In-flight reconnection tokens are generated using cryptographically random UUIDs (`uuid4`), scoped strictly to the lifetime of the active room, and destroyed upon match finalization.

### 2.2 Server Authority & Tamper Resistance
- **Authoritative Simulation**: Clients are strictly thin display/input terminals. The server (`online/server/authority.py`) validates the legal action space before applying any mutation to the game board.
- **Clock Authority**: Turn countdowns and match clocks (`GameClock`) are maintained on the server with monotonically increasing timestamps (`time.monotonic()`), preventing client clock tampering or pause exploits.
- **Result Provenance**: Win/loss/draw terminal outcomes and rating adjustments are adjudicated strictly by the server rules engine.

---

## 3. Network & Transport Security

### 3.1 Transport Encryption
- Production deployments must terminate TLS, serving the web platform over **HTTPS** and WebSocket connections over **WSS (WebSocket Secure)**.

### 3.2 HTTP Security Headers
The web platform server enforces defensive headers:
- `Content-Security-Policy`: Restricts script and style execution to self origin (`default-src 'self'`), forbidding untrusted third-party CDNs.
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: SAMEORIGIN`: Prevents clickjacking attacks.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts referrer information leakage.

### 3.3 CORS & Handshake Validation
- REST endpoints and WebSocket upgrade requests validate the `Origin` header against allowed domains or localhost development configurations.

---

## 4. Abuse Mitigation & DoS Protection

### 4.1 Message Size Limits
- Incoming WebSocket frames and REST payloads are restricted to a maximum size of **64 KB** to eliminate memory exhaustion and buffer overflow vectors.

### 4.2 Rate Limiting
- A token-bucket rate limiter enforces an upper bound of **30 messages per second** per connected WebSocket client. Clients exceeding the burst budget are throttled or disconnected.

### 4.3 Input Sanitization & Error Masking
- All JSON payloads are parsed with strict schema validation.
- Internal exception stack traces are never leaked in network error responses. Clients receive structured, generic error codes (`"acao invalida"`, `"sala cheia"`, etc.).

---

## 5. Dependency & Supply Chain Security

- **Zero-Dependency Web Client**: The web platform (`deploy/web/`) is authored purely in standard HTML5 Canvas, modern CSS, and vanilla ES6 JavaScript, without npm package dependencies or CDN script tags.
- **Automated CodeQL Analysis**: Every Pull Request and scheduled weekly run is scanned using GitHub CodeQL for C++ and Python vulnerabilities.
- **Audited Provenance**: Graphic assets are audited in `tools/licensing/game_icons_manifest.json` under CC BY 3.0.
