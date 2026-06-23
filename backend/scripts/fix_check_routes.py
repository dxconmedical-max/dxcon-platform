from pathlib import Path

p = Path("scripts/check_routes.py")
text = p.read_text()

old = """
for route, items in url_map.items():
    if len(items) > 1:
        print("DUPLICATE URL:", route, items)
        errors += 1
"""

new = """
for route, items in url_map.items():

    methods_seen = set()

    for endpoint, methods in items:

        if methods in methods_seen:
            print("REAL DUPLICATE URL:", route, items)
            errors += 1

        methods_seen.add(methods)
"""

text = text.replace(old, new)

p.write_text(text)

print("check_routes upgraded")
