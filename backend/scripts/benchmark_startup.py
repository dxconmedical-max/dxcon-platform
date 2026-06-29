import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


def main():
    print("\n=== DXCON STARTUP BENCHMARK ===\n")

    timings = []

    for index in range(5):
        started = time.perf_counter()
        from app import create_app

        app = create_app()
        client = app.test_client()
        client.get("/api/v1/system/live")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        timings.append(elapsed_ms)
        print(f"startup run {index + 1}: {elapsed_ms}ms")

    average = round(sum(timings) / len(timings), 2)
    print(f"\nAverage startup: {average}ms")
    print("STARTUP BENCHMARK COMPLETE\n")


if __name__ == "__main__":
    main()
