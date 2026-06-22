import requests

BASE = "https://dxcon-ap.onrender.com"

urls = [
    "/api/v1/system/health",
    "/api/v1/system/stats",
    "/api/v1/system/routes",
    "/api/v1/system/backup-status",
    "/api/v1/result-files",
]

print("\n=== DXCON PRODUCTION CHECK ===\n")

for u in urls:
    try:
        r = requests.get(BASE + u, timeout=15)

        if r.status_code == 200:
            print("OK   ", u)
        else:
            print("FAIL ", u, r.status_code)

    except Exception as e:
        print("ERROR", u, str(e))

print("\nPRODUCTION CHECK DONE\n")
