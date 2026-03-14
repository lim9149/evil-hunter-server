# DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
import json
from pathlib import Path
from main import app

out = Path(__file__).resolve().parents[1] / 'reports' / 'openapi_manual_export.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
