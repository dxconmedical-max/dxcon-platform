"""P0-4: plaintext password fallback removed; hash-only authentication."""

from __future__ import annotations

import inspect
import logging
import os
import tempfile
import unittest
import uuid

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_p04_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

from flask_jwt_extended import create_access_token

from app import create_app
from app.core.logging_config import redact_mapping, sanitize_path
from app.core.passwords import (
    HASH_METHOD,
    hash_password,
    is_recognized_password_hash,
    verify_password,
)
from app.extensions.db import db
from app.models.user import User

PASSWORD = "Password123!"
WRONG_PASSWORD = "WrongPass123!"
PLAINTEXT_STORED = "Password123!"


def _sensitive_keys_in(payload) -> list[str]:
    found = []

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                lowered = str(key).lower()
                if lowered in {
                    "password",
                    "password_hash",
                    "password_secret",
                    "credential",
                }:
                    found.append(key)
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)
    return found


class PasswordSecurityP04Tests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["API_AUTH_GATE_ENABLED"] = False
        self.app.config["ALLOW_PUBLIC_REGISTER"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

        self.user = User(
            email=f"p04-{uuid.uuid4().hex[:8]}@test.local",
            role="DOCTOR",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        self.admin = User(
            email=f"p04-admin-{uuid.uuid4().hex[:8]}@test.local",
            role="ADMIN",
            password_hash=hash_password(PASSWORD),
            is_active=True,
        )
        db.session.add_all([self.user, self.admin])
        db.session.commit()
        self.user_id = self.user.id
        self.user_email = self.user.email
        self.user_hash = self.user.password_hash
        self.admin_email = self.admin.email
        self.admin_token = create_access_token(
            identity=self.admin.id,
            additional_claims={"role": "ADMIN", "email": self.admin.email},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, email, password):
        return self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

    def _admin_headers(self):
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json",
        }

    # --- hashing primitive ---

    def test_canonical_hash_is_pbkdf2_sha256(self):
        hashed = hash_password(PASSWORD)
        self.assertTrue(hashed.startswith("pbkdf2:sha256:"))
        self.assertEqual(HASH_METHOD, "pbkdf2:sha256")
        self.assertTrue(is_recognized_password_hash(hashed))
        self.assertTrue(verify_password(hashed, PASSWORD))
        self.assertFalse(verify_password(hashed, WRONG_PASSWORD))
        self.assertNotEqual(hashed, PASSWORD)

    def test_verify_fails_closed_on_missing_or_empty_hash(self):
        self.assertFalse(verify_password(None, PASSWORD))
        self.assertFalse(verify_password("", PASSWORD))
        self.assertFalse(verify_password(hash_password(PASSWORD), ""))
        self.assertFalse(verify_password(hash_password(PASSWORD), None))

    def test_verify_fails_closed_on_malformed_hash(self):
        self.assertFalse(verify_password("pbkdf2:not-a-valid-hash", PASSWORD))
        self.assertFalse(verify_password("pbkdf2:sha256:broken", PASSWORD))
        self.assertFalse(verify_password("not-a-hash-at-all", PASSWORD))
        self.assertFalse(is_recognized_password_hash("Password123!"))
        self.assertFalse(is_recognized_password_hash("x"))

    def test_plaintext_stored_value_cannot_authenticate(self):
        self.assertFalse(verify_password(PLAINTEXT_STORED, PLAINTEXT_STORED))
        self.assertFalse(verify_password("DemoPass123!", "DemoPass123!"))

    def test_plaintext_fallback_path_does_not_exist(self):
        source = inspect.getsource(verify_password)
        self.assertNotIn("password_hash == password", source)
        self.assertNotIn("password == password_hash", source)
        self.assertNotIn("== stored_password", source)
        module_source = inspect.getsource(inspect.getmodule(verify_password))
        self.assertNotIn("password_hash == password", module_source)

        from app.api.auth import routes as auth_routes

        login_source = inspect.getsource(auth_routes.login)
        self.assertIn("verify_password", login_source)
        self.assertNotIn("== password", login_source)
        self.assertNotIn("password ==", login_source)

        from app.web import auth as web_auth

        web_login_source = inspect.getsource(web_auth.login_page)
        self.assertIn("verify_password", web_login_source)
        self.assertNotIn("password_hash ==", web_login_source)

    # --- login ---

    def test_correct_password_valid_hash_login_succeeds(self):
        resp = self._login(self.user_email, PASSWORD)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        body = resp.get_json()
        self.assertTrue(body.get("success"))
        self.assertIn("access_token", body)
        self.assertIn("token", body)

    def test_incorrect_password_is_401(self):
        resp = self._login(self.user_email, WRONG_PASSWORD)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json().get("error"), "Invalid credentials")

    def test_missing_password_hash_login_fails_closed(self):
        user = User(
            email=f"p04-empty-{uuid.uuid4().hex[:8]}@test.local",
            role="PATIENT",
            password_hash="",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        resp = self._login(user.email, PASSWORD)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json().get("error"), "Invalid credentials")

    def test_malformed_password_hash_login_fails_closed(self):
        user = User(
            email=f"p04-badhash-{uuid.uuid4().hex[:8]}@test.local",
            role="PATIENT",
            password_hash="pbkdf2:sha256:not-valid",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        resp = self._login(user.email, PASSWORD)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json().get("error"), "Invalid credentials")

    def test_plaintext_password_field_cannot_login(self):
        user = User(
            email=f"p04-plain-{uuid.uuid4().hex[:8]}@test.local",
            role="PATIENT",
            password_hash=PLAINTEXT_STORED,
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        resp = self._login(user.email, PLAINTEXT_STORED)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json().get("error"), "Invalid credentials")

    def test_login_response_never_returns_password_or_hash(self):
        resp = self._login(self.user_email, PASSWORD)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        leaked = _sensitive_keys_in(resp.get_json())
        self.assertEqual(leaked, [], leaked)

    def test_login_then_jwt_me_still_works(self):
        login = self._login(self.user_email, PASSWORD)
        self.assertEqual(login.status_code, 200, login.get_json())
        token = login.get_json()["access_token"]
        me = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me.status_code, 200, me.get_json())
        payload = me.get_json()
        self.assertEqual(payload["data"]["user"]["email"], self.user_email)
        leaked = _sensitive_keys_in(payload)
        self.assertEqual(leaked, [], leaked)

    # --- registration ---

    def test_registration_stores_hash_not_plaintext(self):
        email = f"p04-reg-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": PASSWORD},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        body = resp.get_json()
        leaked = _sensitive_keys_in(body)
        self.assertEqual(leaked, [], leaked)

        stored = User.query.filter_by(email=email).first()
        self.assertIsNotNone(stored)
        self.assertNotEqual(stored.password_hash, PASSWORD)
        self.assertTrue(stored.password_hash.startswith("pbkdf2:sha256:"))
        self.assertTrue(verify_password(stored.password_hash, PASSWORD))

        login = self._login(email, PASSWORD)
        self.assertEqual(login.status_code, 200, login.get_json())

    # --- admin provisioning ---

    def test_admin_created_user_stores_hash_not_plaintext(self):
        email = f"p04-admin-user-{uuid.uuid4().hex[:8]}@test.local"
        resp = self.client.post(
            "/api/v1/security/users",
            headers=self._admin_headers(),
            json={"email": email, "password": PASSWORD, "role": "PATIENT"},
        )
        self.assertEqual(resp.status_code, 201, resp.get_json())
        body = resp.get_json()
        leaked = _sensitive_keys_in(body)
        self.assertEqual(leaked, [], leaked)

        stored = User.query.filter_by(email=email).first()
        self.assertIsNotNone(stored)
        self.assertNotEqual(stored.password_hash, PASSWORD)
        self.assertTrue(stored.password_hash.startswith("pbkdf2:sha256:"))
        self.assertTrue(verify_password(stored.password_hash, PASSWORD))

    def test_user_apis_never_return_password_or_hash(self):
        admin_list = self.client.get("/api/v1/admin/users", headers=self._admin_headers())
        self.assertEqual(admin_list.status_code, 200, admin_list.get_json())
        self.assertEqual(_sensitive_keys_in(admin_list.get_json()), [])

        security_list = self.client.get(
            "/api/v1/security/users",
            headers=self._admin_headers(),
        )
        self.assertEqual(security_list.status_code, 200, security_list.get_json())
        self.assertEqual(_sensitive_keys_in(security_list.get_json()), [])

    def test_admin_create_still_requires_admin_jwt(self):
        unauth = self.client.post(
            "/api/v1/security/users",
            json={
                "email": f"p04-noauth-{uuid.uuid4().hex[:8]}@test.local",
                "password": PASSWORD,
            },
        )
        self.assertEqual(unauth.status_code, 401)

        doctor_token = create_access_token(
            identity=self.user_id,
            additional_claims={"role": "DOCTOR", "email": self.user_email},
        )
        forbidden = self.client.post(
            "/api/v1/security/users",
            headers={"Authorization": f"Bearer {doctor_token}"},
            json={
                "email": f"p04-doc-{uuid.uuid4().hex[:8]}@test.local",
                "password": PASSWORD,
            },
        )
        self.assertEqual(forbidden.status_code, 403)

    # --- logging ---

    def test_login_logs_do_not_contain_password_or_hash(self):
        captured = []
        handler = logging.Handler()

        def emit(record):
            captured.append(record.getMessage())
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in {"args", "msg", "message"}
            }
            captured.append(str(extra))

        handler.emit = emit
        logger = logging.getLogger()
        logger.addHandler(handler)
        try:
            self._login(self.user_email, PASSWORD)
            self._login(self.user_email, WRONG_PASSWORD)
        finally:
            logger.removeHandler(handler)

        blob = "\n".join(captured)
        self.assertNotIn(PASSWORD, blob)
        self.assertNotIn(WRONG_PASSWORD, blob)
        self.assertNotIn(self.user_hash, blob)

    def test_redact_mapping_hides_password_and_hash(self):
        redacted = redact_mapping(
            {
                "email": "a@b.c",
                "password": PASSWORD,
                "password_hash": hash_password(PASSWORD),
                "nested": {"credential": "secret-value"},
            }
        )
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["password_hash"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["credential"], "[REDACTED]")
        self.assertEqual(redacted["email"], "a@b.c")

        path = sanitize_path("/api/v1/auth/login?email=a@b.c&password=Password123!")
        self.assertIn("password=[REDACTED]", path)
        self.assertNotIn("Password123!", path)

    # --- historical bcrypt hashes are hashes, not plaintext ---

    def test_bcrypt_stored_hash_still_verifies_without_plaintext_compare(self):
        try:
            import bcrypt
        except ImportError:
            self.skipTest("bcrypt not installed")
        hashed = bcrypt.hashpw(PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.assertTrue(is_recognized_password_hash(hashed))
        self.assertTrue(verify_password(hashed, PASSWORD))
        self.assertFalse(verify_password(hashed, WRONG_PASSWORD))


if __name__ == "__main__":
    unittest.main()
