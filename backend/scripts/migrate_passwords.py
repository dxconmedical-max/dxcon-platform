#!/usr/bin/env python3
"""One-time migration: hash plaintext values stored in users.password_hash.

If password_hash already looks like a recognized hash (pbkdf2/scrypt/bcrypt),
the row is left unchanged.

If the column still contains a legacy plaintext password (the previous
verify_password fallback), this script hashes that known plaintext once.

This does NOT recover lost passwords. Accounts whose stored value is neither
a recognized hash nor a usable plaintext must be re-provisioned.
"""

from app import create_app
from app.core.passwords import hash_password, is_recognized_password_hash
from app.extensions.db import db
from app.models.user import User

app = create_app()

with app.app_context():
    users = User.query.all()
    changed = 0
    skipped_empty = 0
    already_hashed = 0

    for user in users:
        current = user.password_hash or ""
        if not current:
            skipped_empty += 1
            continue
        if is_recognized_password_hash(current):
            already_hashed += 1
            continue

        user.password_hash = hash_password(current)
        changed += 1

    db.session.commit()
    print(
        "PASSWORD MIGRATION DONE. "
        f"Changed: {changed} already_hashed: {already_hashed} empty: {skipped_empty}"
    )
