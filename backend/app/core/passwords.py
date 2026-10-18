from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

# Canonical password hashing for human users, API keys, and device ingest secrets.
# New hashes are always Werkzeug PBKDF2-SHA256 (salted).
HASH_METHOD = "pbkdf2:sha256"


def is_recognized_password_hash(value: str | None) -> bool:
    """Return True if value looks like a stored password hash, not plaintext."""
    if not value:
        return False
    if value.startswith(("pbkdf2:", "scrypt:")):
        return True
    # Historical bcrypt hashes from app.services.security / older web login.
    if value.startswith(("$2a$", "$2b$", "$2y$")):
        return True
    return False


def hash_password(password):
    return generate_password_hash(password, method=HASH_METHOD)


def verify_password(password_hash, password):
    """Verify a password against a stored hash. Fail closed on plaintext/unknown values."""
    if not password_hash or not password:
        return False

    if password_hash.startswith(("pbkdf2:", "scrypt:")):
        try:
            return check_password_hash(password_hash, password)
        except (ValueError, TypeError):
            return False

    if password_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            import bcrypt

            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except (ValueError, TypeError, AttributeError):
            return False

    # No plaintext comparison. Missing/malformed/legacy plaintext values cannot authenticate.
    return False
