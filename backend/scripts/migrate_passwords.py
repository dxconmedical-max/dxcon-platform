from app import create_app
from app.extensions.db import db
from app.models.user import User
from app.core.passwords import hash_password

app = create_app()

with app.app_context():
    users = User.query.all()
    changed = 0

    for user in users:
        current = user.password_hash or ""

        if current.startswith("scrypt:") or current.startswith("pbkdf2:"):
            continue

        user.password_hash = hash_password(current)
        changed += 1

    db.session.commit()

    print(f"PASSWORD MIGRATION DONE. Changed: {changed}")
