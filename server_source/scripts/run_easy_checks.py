# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_DIR = ROOT / 'reports'
REPORT_DIR.mkdir(exist_ok=True)


def run_pytest() -> dict:
    cmd = [sys.executable, '-m', 'pytest', '-q']
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        'name': 'pytest',
        'ok': proc.returncode == 0,
        'returncode': proc.returncode,
        'stdout_tail': proc.stdout[-2000:],
        'stderr_tail': proc.stderr[-2000:],
    }


def run_smoke() -> dict:
    os.environ.setdefault('SQLITE_PATH', ':memory:')
    from main import app

    client = TestClient(app)
    steps = []

    def check(name: str, condition: bool, detail: str = ''):
        steps.append({'step': name, 'ok': bool(condition), 'detail': detail})
        if not condition:
            raise AssertionError(f'{name} failed: {detail}')

    r = client.get('/health')
    check('health', r.status_code == 200, r.text)

    r = client.post('/auth/guest', json={'deviceId': 'smoke-device'})
    check('guest_login', r.status_code == 200, r.text)
    body = r.json()
    account_id = body.get('accountId', 'acc_smoke')

    monster = {
        'monsterId': 'm_smoke', 'name': 'Training Slime', 'level': 1,
        'hp': 50, 'atk': 5, 'defense': 0, 'goldPerMin': 2, 'expPerMin': 1,
    }
    r = client.post('/monsters', json=monster)
    check('seed_monster', r.status_code == 200, r.text)

    hunter = {
        'hunterId': 'h_smoke', 'accountId': account_id, 'slotIndex': 0, 'name': 'SmokeHero',
        'jobId': 'novice', 'level': 1, 'exp': 0, 'powerScore': 10, 'hp': 100, 'atk': 10, 'defense': 1,
    }
    r = client.post('/hunters', json=hunter)
    check('create_hunter', r.status_code == 200, r.text)

    r = client.post('/combat/fight', json={'hunterId': 'h_smoke', 'monsterId': 'm_smoke', 'buffs': {'atkMul': 1.0}})
    check('combat_fight', r.status_code == 200, r.text)

    return {'name': 'smoke', 'ok': True, 'steps': steps}


def export_openapi() -> dict:
    from main import app
    data = app.openapi()
    path = REPORT_DIR / 'openapi_snapshot.json'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'name': 'openapi_export', 'ok': True, 'file': str(path.relative_to(ROOT))}


def main() -> int:
    results = [run_pytest()]
    if results[0]['ok']:
        try:
            results.append(run_smoke())
            results.append(export_openapi())
        except Exception as exc:  # noqa: BLE001
            results.append({'name': 'smoke', 'ok': False, 'error': str(exc)})

    overall_ok = all(item.get('ok') for item in results)
    report = {
        'overall_ok': overall_ok,
        'results': results,
    }
    out_path = REPORT_DIR / 'easy_check_report.json'
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f'\nSaved report -> {out_path}')
    return 0 if overall_ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
