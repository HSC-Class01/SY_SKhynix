from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _records(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    frame = pd.read_csv(path)
    return json.loads(frame.to_json(orient="records"))


def build(root: Path = ROOT) -> dict[str, Any]:
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    metrics = _records(root / "data" / "metrics.csv")
    reports = _records(root / "data" / "reports.csv")
    peers = _records(root / "data" / "peers.csv")
    period_order = {"Q1": 1, "H1": 2, "Q3": 3, "FY": 4}
    report_code = {"FY": "11011", "H1": "11012", "Q1": "11013", "Q3": "11014"}
    for row in metrics:
        row.setdefault("period_order", period_order.get(str(row.get("period")), 9))
        row.setdefault("report_code", report_code.get(str(row.get("period"))))
        row.setdefault("fs_div", "CFS")
    payload = {
        "company": config["company_name"],
        "stock_code": config["stock_code"],
        "start_year": config.get("start_year", 2010),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "reports": reports,
        "peers": peers,
    }
    docs = root
    docs.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    output = docs / "dashboard-data.js"
    output.write_text(f"window.DASHBOARD_DATA = {serialized};\n", encoding="utf-8")
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "dashboard-data.js").write_text(
        f"window.DASHBOARD_DATA = {serialized};\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(output), "metrics": len(metrics)}, ensure_ascii=False))
    return payload


if __name__ == "__main__":
    build()


