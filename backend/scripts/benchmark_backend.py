import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app


def benchmark(client, path, iterations=20):
    durations = []
    for _ in range(iterations):
        started = time.perf_counter()
        response = client.get(path)
        durations.append((time.perf_counter() - started) * 1000)
        if response.status_code >= 500:
            raise RuntimeError(f"{path} returned {response.status_code}")

    durations.sort()
    return {
        "path": path,
        "iterations": iterations,
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
        "avg_ms": round(statistics.mean(durations), 2),
        "p95_ms": round(durations[max(int(len(durations) * 0.95) - 1, 0)], 2),
    }


def main():
    print("\n=== DXCON BACKEND BENCHMARK ===\n")

    app = create_app()
    client = app.test_client()

    targets = [
        "/api/v1/system/health",
        "/api/v1/system/metrics",
        "/api/v1/system/performance",
    ]

    for path in targets:
        result = benchmark(client, path)
        print(
            f"{result['path']}: avg={result['avg_ms']}ms "
            f"p95={result['p95_ms']}ms min={result['min_ms']}ms max={result['max_ms']}ms"
        )

    print("\nBENCHMARK COMPLETE\n")


if __name__ == "__main__":
    main()
