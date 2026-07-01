from flask import Blueprint, current_app, render_template_string

from app.services.api_platform_service import ApiClientService, ApiKeyService, ApiPlatformService


api_platform_web_bp = Blueprint("api_platform_web", __name__)


def _cdn(kind):
    base = current_app.config.get("OPENAPI_DOCS_CDN", "").rstrip("/")
    if not base:
        return None
    assets = {
        "swagger": f"{base}/swagger-ui-bundle.min.js",
        "redoc": f"{base}/redoc.standalone.js",
    }
    return assets.get(kind)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #102a43; color: #fff; padding: 20px; }
    .sidebar a { color: #d9e2ec; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #d9e2ec; padding: 8px; text-align: left; vertical-align: top; }
    .card { background: #fff; padding: 16px; margin-bottom: 16px; border: 1px solid #d9e2ec; }
    pre { background: #0b1727; color: #d9e2ec; padding: 12px; overflow: auto; }
    code { background: #eef2f7; padding: 2px 4px; }
    </style>
    """


def _dev_sidebar(active):
    links = [
        ("/developer", "Overview"),
        ("/developer/api-keys", "API Keys"),
        ("/developer/routes", "Routes"),
        ("/developer/sandbox", "Sandbox"),
        ("/api-docs", "API Docs"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Developer Portal</h2>{items}</div>'


DOCS_INDEX = """
<!DOCTYPE html><html><head><title>DxCon API Docs</title>{styles}</head><body>
<div class="layout"><div class="sidebar"><h2>DxCon API Docs</h2>
<a href="/api-docs/swagger">Swagger UI</a>
<a href="/api-docs/redoc">ReDoc</a>
<a href="/api/v1/openapi.json">OpenAPI JSON</a>
<a href="/api/v1/openapi.yaml">OpenAPI YAML</a>
<a href="/developer">Developer Portal</a>
</div><div class="content"><h1>API Documentation</h1>
<div class="card"><p>Stable external API platform for partners, labs, hospitals, and clinics.</p>
<p>OpenAPI version: <code>v1</code></p></div></div></div></body></html>
"""

SWAGGER_TEMPLATE = """
<!DOCTYPE html><html><head><title>Swagger UI</title>{styles}</head><body>
<div class="content"><h1>Swagger UI</h1>
<div id="swagger-ui"></div>
<script>{cdn_script}
const specUrl = '/api/v1/openapi.json';
if (window.SwaggerUIBundle) {{
  SwaggerUIBundle({{ url: specUrl, dom_id: '#swagger-ui' }});
}} else {{
  fetch(specUrl).then(r => r.json()).then(spec => {{
    const paths = Object.keys(spec.paths || {{}}).slice(0, 100);
    document.getElementById('swagger-ui').innerHTML =
      '<div class="card"><h2>Built-in Explorer</h2><table><tr><th>Path</th><th>Methods</th></tr>' +
      paths.map(p => '<tr><td>' + p + '</td><td>' + Object.keys(spec.paths[p]).join(', ') + '</td></tr>').join('') +
      '</table></div>';
  }});
}}
</script></body></html>
"""

REDOC_TEMPLATE = """
<!DOCTYPE html><html><head><title>ReDoc</title>{styles}</head><body>
<div class="content"><h1>ReDoc</h1><div id="redoc"></div>
<script>{cdn_script}
const specUrl = '/api/v1/openapi.json';
if (window.Redoc) {{
  Redoc.init(specUrl, {{}}, document.getElementById('redoc'));
}} else {{
  fetch(specUrl).then(r => r.json()).then(spec => {{
    document.getElementById('redoc').innerHTML =
      '<div class="card"><h2>' + spec.info.title + ' ' + spec.info.version + '</h2>' +
      '<p>' + (spec.info.description || '') + '</p>' +
      '<p>Paths: ' + Object.keys(spec.paths || {{}}).length + '</p></div>';
  }});
}}
</script></body></html>
"""


@api_platform_web_bp.route("/api-docs")
def api_docs_index():
    return render_template_string(DOCS_INDEX.format(styles=_styles()))


@api_platform_web_bp.route("/api-docs/swagger")
def api_docs_swagger():
    cdn = _cdn("swagger")
    cdn_script = ""
    if cdn:
        cdn_script = f'<script src="{cdn}"></script>'
    return render_template_string(SWAGGER_TEMPLATE.format(styles=_styles(), cdn_script=cdn_script))


@api_platform_web_bp.route("/api-docs/redoc")
def api_docs_redoc():
    cdn = _cdn("redoc")
    cdn_script = ""
    if cdn:
        cdn_script = f'<script src="{cdn}"></script>'
    return render_template_string(REDOC_TEMPLATE.format(styles=_styles(), cdn_script=cdn_script))


@api_platform_web_bp.route("/developer")
def developer_home():
    ApiClientService.ensure_defaults()
    health = ApiPlatformService.health(current_app._get_current_object())
    return f"""<!DOCTYPE html><html><head><title>Developer Portal</title>{_styles()}</head><body>
    <div class="layout">{_dev_sidebar("/developer")}<div class="content">
    <h1>Developer Portal</h1>
    <div class="card"><strong>Platform status:</strong> {health["status"]}<br>
    <strong>Routes:</strong> {health["summary"]["total"]}<br>
    <strong>Domains:</strong> use <code>/developer/routes</code></div>
    </div></div></body></html>"""


@api_platform_web_bp.route("/developer/api-keys")
def developer_api_keys():
    ApiClientService.ensure_defaults()
    keys = ApiKeyService.list_keys()
    table = "".join(
        f"<tr><td>{row['key_prefix']}...</td><td>{row['status']}</td><td>{row['client_id']}</td></tr>"
        for row in keys["keys"]
    )
    return f"""<!DOCTYPE html><html><head><title>API Keys</title>{_styles()}</head><body>
    <div class="layout">{_dev_sidebar("/developer/api-keys")}<div class="content">
    <h1>API Keys</h1>
    <table><tr><th>Prefix</th><th>Status</th><th>Client</th></tr>{table or "<tr><td colspan='3'>No keys</td></tr>"}</table>
    </div></div></body></html>"""


@api_platform_web_bp.route("/developer/routes")
def developer_routes():
    inventory = ApiPlatformService.inventory(current_app._get_current_object())
    rows = inventory["inventory"]["routes"][:50]
    table = "".join(
        f"<tr><td>{','.join(row['methods'])}</td><td>{row['path']}</td><td>{row['blueprint']}</td></tr>"
        for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Routes</title>{_styles()}</head><body>
    <div class="layout">{_dev_sidebar("/developer/routes")}<div class="content">
    <h1>Route Catalog</h1>
    <div class="card">Showing first 50 of {inventory['inventory']['count']} routes</div>
    <table><tr><th>Methods</th><th>Path</th><th>Blueprint</th></tr>{table}</table>
    </div></div></body></html>"""


@api_platform_web_bp.route("/developer/sandbox")
def developer_sandbox():
    return f"""<!DOCTYPE html><html><head><title>Sandbox</title>{_styles()}</head><body>
    <div class="layout">{_dev_sidebar("/developer/sandbox")}<div class="content">
    <h1>Developer Sandbox</h1>
    <div class="card">
    <p>Send test requests with:</p>
    <pre>POST /api/v1/developer/sandbox/request
{{ "method": "GET", "path": "/api/v1/api-platform/health" }}</pre>
    </div></div></div></body></html>"""
