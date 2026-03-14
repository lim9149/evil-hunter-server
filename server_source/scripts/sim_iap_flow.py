# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import requests, time, secrets
BASE="http://127.0.0.1:8000"

def main():
    g = requests.post(f"{BASE}/auth/guest", json={"deviceId":"device-iap"}).json()
    token = g["accessToken"]
    headers={"Authorization": f"Bearer {token}", "X-Req-TS": str(int(time.time())), "X-Req-Nonce": secrets.token_hex(8)}

    payload={"productId":"gems_100","purchaseToken":"ptok","txId":"order-1","raw":{"debug":"yes"}}
    r = requests.post(f"{BASE}/iap/google/verify", json=payload, headers=headers)
    print("iap verify:", r.status_code, r.json())

if __name__=="__main__":
    main()