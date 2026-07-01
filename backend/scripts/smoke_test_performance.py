import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app


def main():
    print("\n=== DXCON PERFORMANCE SMOKE TEST ===\n")
    errors = 0

    app = create_app()
    client = app.test_client()

    for label, path in [
        ("health", "/api/v1/system/health"),
        ("performance", "/api/v1/system/performance"),
    ]:
        response = client.get(path)
        if response.status_code == 200:
            print(f"OK: {label} responds")
        else:
            print(f"FAIL: {label}", response.status_code)
            errors += 1

    if errors:
        print("\nPERFORMANCE SMOKE TEST FAILED:", errors, "issue(s)")
        sys.exit(1)

    print("\nPERFORMANCE SMOKE TEST PASSED\n")


if __name__ == "__main__":
    main()
