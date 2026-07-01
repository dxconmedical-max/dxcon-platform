from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password_hash, password):
    if not password_hash or not password:
        return False

    if password_hash.startswith("scrypt:") or password_hash.startswith("pbkdf2:"):
        return check_password_hash(password_hash, password)

    # Temporary backward compatibility for old demo users using plain text.
    return password_hash == password
