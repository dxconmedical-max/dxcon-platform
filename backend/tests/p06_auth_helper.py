"""P0-6 test helper: inject JWT into an existing Flask test client."""

from __future__ import annotations

import uuid

from flask_jwt_extended import create_access_token

from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User


class AuthInjectingClient:
    """Delegates to Flask's test client, defaulting Authorization to a JWT."""

    def __init__(self, client, token: str):
        self._client = client
        self._token = token

    def _merge(self, kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {self._token}")
        kwargs["headers"] = headers
        return kwargs

    def get(self, *args, **kwargs):
        return self._client.get(*args, **self._merge(kwargs))

    def post(self, *args, **kwargs):
        return self._client.post(*args, **self._merge(kwargs))

    def put(self, *args, **kwargs):
        return self._client.put(*args, **self._merge(kwargs))

    def patch(self, *args, **kwargs):
        return self._client.patch(*args, **self._merge(kwargs))

    def delete(self, *args, **kwargs):
        return self._client.delete(*args, **self._merge(kwargs))

    def __getattr__(self, name):
        return getattr(self._client, name)


def attach_admin_client(test_case, *, role: str = "ADMIN"):
    """Create an active user and wrap ``test_case.client`` with JWT injection.

    Public endpoints ignore the extra Authorization header. Call after
    ``db.create_all()`` inside an app context.
    """
    user = User(
        email=f"p06-{role.lower()}-{uuid.uuid4().hex[:8]}@test.local",
        role=role,
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role, "email": user.email},
    )
    test_case.auth_user = user
    test_case.auth_token = token
    test_case.raw_client = test_case.client
    test_case.client = AuthInjectingClient(test_case.client, token)
    return user, token
