from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .dart_client import DartAPIError, DartClient, NO_DATA_STATUS


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"
DATA_DIR = ROOT / "data"

REPORTS = (
    ("11011", "FY", "annual", 4),
    ("11012", "H1", "half-year", 2),
    ("11013", "Q1", "quarterly", 1),
    ("11014", "Q3", "quarterly", 3),
)
ACCOUNT_COLUMNS = (
    "sj_div",
    "account_id",
    "account_nm",
    "thstrm_amount",
    "thstrm_add_amount",
    "thstrm_nm",
    "currency",
)


def _fetch_with_fallback(
    client: DartClient,
    corp_code: str,
    year: int,
    report_code: str,
) -> tuple[dict[str, Any], str]:
    last_error: DartAPIError | None = None
    for fs_div in ("CFS", "OFS"):
        try:
            return (
                client.financial_statement(corp_code, year, report_code, fs_div),
                fs_div,
            )
        except DartAPIError as exc:
            last_error = exc
            if exc.status != NO_DATA_STATUS:
                raise
    assert last_error is not None
    raise last_error


def collect(
    root: Path = ROOT,
    client: DartClient | None = None,
    now_year: int | None = None,
) -> dict[str, int]:
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    client = client or DartClient.from_environment()
    end_year = now_year or datetime.now().year
    start_year = int(config.get("start_year", 2010))
    if start_year > end_year:
        raise ValueError("start_year가 현재 연도보다 큽니다.")

    data_dir = root / "data"
    source_path = data_dir / "financial_statements.csv"
    reports_path = data_dir / "reports.csv"
    preserved_accounts: list[dict[str, Any]] = []
    preserved_reports: list[dict[str, Any]] = []
    refresh_start_year = start_year
    if source_path.exists() and source_path.stat().st_size > 0:
        existing = pd.read_csv(source_path, dtype={"report_code": str})
        if not existing.empty:
            refresh_years = max(1, int(config.get("refresh_years", 2)))
            refresh_start_year = max(start_year, end_year - refresh_years + 1)
            preserved_accounts = existing[
                existing["year"].astype(int) < refresh_start_year
            ].to_dict(orient="records")
            if reports_path.exists() and reports_path.stat().st_size > 0:
                existing_reports = pd.read_csv(
                    reports_path, dtype={"report_code": str}
                )
                if not existing_reports.empty:
                    preserved_reports = existing_reports[
                        existing_reports["year"].astype(int) < refresh_start_year
                    ].to_dict(orient="records")

    corp_code = client.corp_code_for_stock(str(config["stock_code"]))
    accounts: list[dict[str, Any]] = preserved_accounts
    reports: list[dict[str, Any]] = preserved_reports
    summary = {"saved": 0, "missing": 0}

    for year in range(refresh_start_year, end_year + 1):
        for report_code, period, category, period_order in REPORTS:
            base = {
                "year": year,
                "period": period,
                "period_order": period_order,
                "category": category,
                "report_code": report_code,
            }
            try:
                payload, fs_div = _fetch_with_fallback(
                    client, corp_code, year, report_code
                )
            except DartAPIError as exc:
                if exc.status != NO_DATA_STATUS:
                    raise
                reports.append({**base, "fs_div": None, "status": "missing"})
                summary["missing"] += 1
                continue

            rows = payload.get("list", [])
            for account in rows:
                accounts.append(
                    {
                        **base,
                        **{column: account.get(column) for column in ACCOUNT_COLUMNS},
                        "fs_div": fs_div,
                    }
                )
            reports.append(
                {**base, "fs_div": fs_div, "status": "saved", "accounts": len(rows)}
            )
            summary["saved"] += 1
            time.sleep(0.12)

    data_dir.mkdir(parents=True, exist_ok=True)
    account_columns = [
        "year", "period", "period_order", "category", "report_code",
        "fs_div", *ACCOUNT_COLUMNS,
    ]
    report_columns = [
        "year", "period", "period_order", "category", "report_code",
        "fs_div", "status", "accounts",
    ]
    pd.DataFrame(accounts, columns=account_columns).to_csv(
        data_dir / "financial_statements.csv", index=False
    )
    pd.DataFrame(reports, columns=report_columns).to_csv(
        data_dir / "reports.csv", index=False
    )
    print(json.dumps({"company": config["company_name"], **summary}, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    collect()

