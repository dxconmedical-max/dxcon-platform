#!/usr/bin/env python3
"""Generate lightweight SDK stubs for DxCon API Platform."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_ROOT = ROOT / "generated_api" / "sdk"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.api_platform.route_catalog import build_catalog
from app.api_platform.api_inventory import scan_routes


def _stub_name(path: str, method: str) -> str:
    clean = path.replace("/api/v1/", "").replace("<", "").replace(">", "").replace("/", "_").replace("-", "_")
    return f"{method.lower()}_{clean}".strip("_")


def generate_python_stubs(routes, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        '"""Auto-generated lightweight DxCon Python SDK stub."""',
        "",
        "import json",
        "from urllib import request, error",
        "",
        "",
        "class DxConApiError(Exception):",
        "    def __init__(self, status_code, payload):",
        "        super().__init__(payload.get('error', payload))",
        "        self.status_code = status_code",
        "        self.payload = payload",
        "",
        "",
        "class DxConClient:",
        "    def __init__(self, base_url='http://localhost:5000', api_key=None):",
        "        self.base_url = base_url.rstrip('/')",
        "        self.api_key = api_key",
        "",
        "    def _headers(self, extra=None):",
        "        headers = {'Content-Type': 'application/json'}",
        "        if self.api_key:",
        "            headers['X-API-Key'] = self.api_key",
        "        if extra:",
        "            headers.update(extra)",
        "        return headers",
        "",
        "    def request(self, method, path, body=None, headers=None):",
        "        url = self.base_url + path",
        "        data = None if body is None else json.dumps(body).encode('utf-8')",
        "        req = request.Request(url, data=data, headers=self._headers(headers), method=method.upper())",
        "        try:",
        "            with request.urlopen(req) as resp:",
        "                raw = resp.read().decode('utf-8')",
        "                return json.loads(raw) if raw else {}",
        "        except error.HTTPError as exc:",
        "            payload = json.loads(exc.read().decode('utf-8') or '{}')",
        "            raise DxConApiError(exc.code, payload) from exc",
        "",
    ]

    for route in routes[:40]:
        for method in route["methods"]:
            name = _stub_name(route["path"], method)
            lines.extend(
                [
                    f"    def {name}(self, **kwargs):",
                    f"        return self.request('{method}', '{route['path']}', body=kwargs.get('body'), headers=kwargs.get('headers'))",
                    "",
                ]
            )

    (output_dir / "dxcon_client.py").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_typescript_stubs(routes, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "/** Auto-generated lightweight DxCon TypeScript SDK stub. */",
        "",
        "export class DxConApiError extends Error {",
        "  statusCode: number;",
        "  payload: Record<string, unknown>;",
        "  constructor(statusCode: number, payload: Record<string, unknown>) {",
        "    super(JSON.stringify(payload));",
        "    this.statusCode = statusCode;",
        "    this.payload = payload;",
        "  }",
        "}",
        "",
        "export class DxConClient {",
        "  baseUrl: string;",
        "  apiKey?: string;",
        "",
        "  constructor(baseUrl = 'http://localhost:5000', apiKey?: string) {",
        "    this.baseUrl = baseUrl.replace(/\\/$/, '');",
        "    this.apiKey = apiKey;",
        "  }",
        "",
        "  async request(method: string, path: string, body?: unknown, headers: Record<string, string> = {}) {",
        "    const finalHeaders: Record<string, string> = { 'Content-Type': 'application/json', ...headers };",
        "    if (this.apiKey) finalHeaders['X-API-Key'] = this.apiKey;",
        "    const response = await fetch(`${this.baseUrl}${path}`, {",
        "      method: method.toUpperCase(),",
        "      headers: finalHeaders,",
        "      body: body === undefined ? undefined : JSON.stringify(body),",
        "    });",
        "    const payload = await response.json().catch(() => ({}));",
        "    if (!response.ok) throw new DxConApiError(response.status, payload as Record<string, unknown>);",
        "    return payload;",
        "  }",
        "",
    ]

    for route in routes[:40]:
        for method in route["methods"]:
            name = _stub_name(route["path"], method)
            lines.extend(
                [
                    f"  async {name}(body?: unknown) {{",
                    f"    return this.request('{method}', '{route['path']}', body);",
                    "  }",
                    "",
                ]
            )

    lines.append("}")
    (output_dir / "dxcon_client.ts").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    app = create_app()
    inventory = scan_routes(app)
    catalog = build_catalog(inventory["routes"])
    manifest = {
        "route_count": inventory["count"],
        "domain_count": catalog["domain_count"],
        "domains": [item["domain"] for item in catalog["domains"][:20]],
    }
    python_dir = SDK_ROOT / "python"
    typescript_dir = SDK_ROOT / "typescript"
    generate_python_stubs(inventory["routes"], python_dir)
    generate_typescript_stubs(inventory["routes"], typescript_dir)
    (SDK_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("WROTE:", python_dir / "dxcon_client.py")
    print("WROTE:", typescript_dir / "dxcon_client.ts")
    print("WROTE:", SDK_ROOT / "manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
