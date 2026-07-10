# Partner API Security

API credentials: `POST /api/v1/integration/credentials`

- Raw keys shown once at creation
- Stored as SHA-256 hash only
- Scoped permissions (orders.read, results.read, webhooks.manage, etc.)
- Optional IP allowlist
- Revocation via credential ID

Never log API keys or clinical payloads.
