# Mobile Token Security

## Storage

- Access and refresh tokens stored in **flutter_secure_storage** (Keychain / EncryptedSharedPreferences).
- Token expiry metadata stored alongside tokens.
- Active organization ID stored as minimal context identifier.

## Never stored

- Passwords
- Full patient records
- Report PDFs (unencrypted)
- Payment secrets

## Session lifecycle

1. Login → persist tokens via secure storage.
2. API calls → Bearer access token; refresh on 401 via `/api/v1/auth/refresh`.
3. Logout → remote logout with refresh token, then `deleteAll()` on secure storage.
4. Organization switch → update org context; clear tenant-scoped Hive caches.

## Logging

Application logs must not include tokens, passwords, or clinical payloads.
`SafeLogger` redacts known sensitive patterns.

## Limitations

- Certificate pinning is prepared but not enabled by default.
- Jailbreak/root detection is foundation-only.
