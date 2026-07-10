"""Typed AI Platform SDK — Release 3.0 Epic 9."""

from __future__ import annotations

from typing import Any


class AIPlatformClient:
    def __init__(self, http_client, *, token: str | None = None, organization_id: str | None = None):
        self._http = http_client
        self._token = token
        self._organization_id = organization_id
        self.base_path = "/api/v1/ai-platform"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._organization_id:
            headers["X-Organization-Id"] = self._organization_id
        return headers

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._http.post(f"{self.base_path}/infer", json=payload, headers=self._headers())

    def create_memory_session(self, context_type: str = "GENERAL") -> dict[str, Any]:
        return self._http.post(
            f"{self.base_path}/memory/sessions",
            json={"context_type": context_type},
            headers=self._headers(),
        )

    def rag_retrieve(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        return self._http.post(
            f"{self.base_path}/rag/retrieve",
            json={"query": query, "limit": limit},
            headers=self._headers(),
        )

    def list_audit(self, *, page: int = 1) -> dict[str, Any]:
        return self._http.get(f"{self.base_path}/audit?page={page}", headers=self._headers())

    def sdk_manifest(self) -> dict[str, Any]:
        return self._http.get(f"{self.base_path}/sdk/manifest", headers={"Accept": "application/json"})
