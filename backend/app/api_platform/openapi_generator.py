import json
from pathlib import Path

from app.api_platform.api_inventory import scan_routes
from app.api_platform.openapi_schema import base_openapi_document, operation_object
from app.api_platform.route_catalog import _domain_from_path
from app.api_platform.versioning import route_metadata

GENERATED_DIR = Path(__file__).resolve().parents[2] / "generated_api"


def _to_yaml(value, indent=0):
    space = "  " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{space}{key}:")
                lines.append(_to_yaml(item, indent + 1))
            else:
                lines.append(f"{space}{key}: {_yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{space}-")
                lines.append(_to_yaml(item, indent + 1))
            else:
                lines.append(f"{space}- {_yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{space}{_yaml_scalar(value)}"


def _yaml_scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\n", "\\n")
    if any(char in text for char in [":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!"]) or text == "":
        return json.dumps(text)
    return text


def build_openapi(app, servers=None):
    inventory = scan_routes(app)
    document = base_openapi_document(servers=servers)
    tags = set()

    for route in inventory["routes"]:
        path = route["path"].replace("<", "{").replace(">", "}")
        domain = _domain_from_path(route["path"])
        tags.add(domain)
        meta = route_metadata(route["path"])
        document["paths"].setdefault(path, {})
        for method in route["methods"]:
            document["paths"][path][method.lower()] = operation_object(
                method,
                domain,
                route["path"],
                deprecated=meta.get("deprecated", False),
            )

    document["tags"] = [{"name": tag, "description": f"{tag} API routes"} for tag in sorted(tags)]
    document["x-inventory"] = inventory["summary"]
    return document


def write_openapi_artifacts(app, output_dir=None):
    output_dir = Path(output_dir or GENERATED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    document = build_openapi(app)
    json_path = output_dir / "openapi.json"
    yaml_path = output_dir / "openapi.yaml"
    json_path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    yaml_path.write_text(_to_yaml(document) + "\n", encoding="utf-8")
    return {"json": str(json_path), "yaml": str(yaml_path), "paths": len(document.get("paths", {}))}
