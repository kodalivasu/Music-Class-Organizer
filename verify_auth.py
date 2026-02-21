"""Quick verification: unauthenticated GET/POST to API should return 401."""
import urllib.request
import urllib.error

def main():
    base = "http://127.0.0.1:8000"
    ok = True
    # GET /api/categories
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"{base}/api/categories"), timeout=5)
        print(f"GET /api/categories: {r.status} (expected 401)")
        ok = False
    except urllib.error.HTTPError as e:
        print(f"GET /api/categories: {e.code} (expected 401)")
        if e.code != 401:
            ok = False
    except Exception as e:
        print(f"GET /api/categories error: {e}")
        ok = False
    # POST /api/update-file
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(
                f"{base}/api/update-file",
                data=b"{}",
                method="POST",
                headers={"Content-Type": "application/json"},
            ),
            timeout=5,
        )
        print(f"POST /api/update-file: {r.status} (expected 401)")
        ok = False
    except urllib.error.HTTPError as e:
        print(f"POST /api/update-file: {e.code} (expected 401)")
        if e.code != 401:
            ok = False
    except Exception as e:
        print(f"POST /api/update-file error: {e}")
        ok = False
    print("Verification OK." if ok else "Verification FAILED.")
    return 0 if ok else 1

if __name__ == "__main__":
    exit(main())
