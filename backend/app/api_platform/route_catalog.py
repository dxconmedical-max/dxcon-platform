from collections import defaultdict


def _domain_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
        return parts[2]
    return "root"


def build_catalog(routes):
    domains = defaultdict(list)
    for route in routes:
        domain = _domain_from_path(route["path"])
        domains[domain].append(route)

    catalog = []
    for domain in sorted(domains.keys()):
        items = sorted(domains[domain], key=lambda row: row["path"])
        catalog.append(
            {
                "domain": domain,
                "route_count": len(items),
                "routes": items,
            }
        )
    return {
        "domain_count": len(catalog),
        "domains": catalog,
    }
