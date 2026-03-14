# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import requests

BASE = "http://127.0.0.1:8000"

def main():
    r = requests.post(f"{BASE}/auth/guest", json={"deviceId": "device-abc"})
    print("guest login:", r.status_code, r.json())

if __name__ == "__main__":
    main()