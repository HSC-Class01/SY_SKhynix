from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analyze import analyze
from src.collect import collect
from src.dart_client import DartAPIError
from src.dashboard import build


class FakeDartClient:
    def corp_code_for_stock(self, stock_code: str) -> str:
        return "00164779"

    def financial_statement(
        self, corp_code: str, business_year: int, report_code: str, fs_div: str
    ) -> dict:
        if report_code != "11011" or fs_div == "CFS":
            raise DartAPIError("자료 없음", status="013")
        return {
            "list": [
                {"account_nm": "매출액", "thstrm_amount": "1000000000000"},
                {"account_nm": "영업이익", "thstrm_amount": "200000000000"},
                {"account_nm": "당기순이익", "thstrm_amount": "150000000000"},
                {"account_nm": "자산총계", "thstrm_amount": "3000000000000"},
                {"account_nm": "부채총계", "thstrm_amount": "1200000000000"},
                {"account_nm": "자본총계", "thstrm_amount": "1800000000000"},
            ]
        }


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "config.json").write_text(
            json.dumps({
                "company_name": "SK hynix", "stock_code": "000660",
                "start_year": 2025, "peer_firms": [],
            }),
            encoding="utf-8",
        )
        (self.root / "data" / "peers.csv").write_text(
            "기업명,종목코드,비교 목적\n삼성전자,005930,메모리 비교\n",
            encoding="utf-8-sig",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_full_pipeline_with_cfs_to_ofs_fallback(self) -> None:
        summary = collect(self.root, FakeDartClient(), now_year=2025)
        self.assertEqual(summary, {"saved": 1, "missing": 3})

        reports = pd.read_csv(self.root / "data" / "reports.csv")
        self.assertEqual(len(reports), 4)
        self.assertEqual(reports.iloc[0]["fs_div"], "OFS")

        metrics = analyze(self.root)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics.iloc[0]["operating_margin_pct"], 20.0)
        self.assertAlmostEqual(metrics.iloc[0]["debt_to_equity_pct"], 66.67)

        payload = build(self.root)
        self.assertEqual(len(payload["metrics"]), 1)
        self.assertIn(
            "window.DASHBOARD_DATA = ",
            (self.root / "docs" / "dashboard-data.js").read_text(encoding="utf-8"),
        )

    def test_analyze_creates_empty_output_without_source(self) -> None:
        frame = analyze(self.root)
        self.assertTrue(frame.empty)
        self.assertTrue((self.root / "data" / "metrics.csv").exists())

    def test_q3_cumulative_income_and_cash_flow_are_converted_to_quarter(self) -> None:
        rows = []
        for period, order, revenue, revenue_ytd, operating_income, operating_ytd, net_income, net_ytd, cash_flow in (
            ("Q1", 1, 300, 300, 30, 30, 10, 10, 20),
            ("H1", 2, 300, None, 30, None, 10, None, 60),
            ("Q3", 3, 300, 900, 60, 120, 30, 50, 90),
        ):
            for name, amount, sj_div in (
                ("매출액", revenue, "IS"),
                ("영업이익", operating_income, "IS"),
                ("분기순이익" if period in {"Q1", "Q3"} else "반기순이익", net_income, "IS"),
                ("자산총계", 1000, "BS"),
                ("부채총계", 400, "BS"),
                ("자본총계", 600, "BS"),
                ("영업활동현금흐름", cash_flow, "CF"),
            ):
                rows.append({
                    "year": 2025, "period": period, "period_order": order,
                    "category": "half-year" if period == "H1" else "quarterly",
                    "report_code": "11012" if period == "H1" else "11014",
                    "fs_div": "CFS", "sj_div": sj_div,
                    "account_nm": name, "thstrm_amount": amount,
                    "thstrm_add_amount": (
                        revenue_ytd if name == "매출액" else
                        operating_ytd if name == "영업이익" else
                        net_ytd if name in {"반기순이익", "분기순이익"} else None
                    ),
                })
        pd.DataFrame(rows).to_csv(self.root / "data" / "financial_statements.csv", index=False)
        metrics = analyze(self.root).set_index("period")
        self.assertEqual(metrics.loc["H1", "revenue"], 600)
        self.assertEqual(metrics.loc["H1", "operating_income"], 60)
        self.assertEqual(metrics.loc["Q3", "revenue"], 300)
        self.assertEqual(metrics.loc["Q3", "operating_income"], 60)
        self.assertEqual(metrics.loc["H1", "net_income"], 20)
        self.assertEqual(metrics.loc["Q3", "net_income"], 30)
        self.assertEqual(metrics.loc["Q3", "operating_cash_flow"], 30)

        source = self.root / "data" / "financial_statements.csv"
        collected = pd.read_csv(source)
        for account, amount in (("매출액", 650), ("영업이익", 65), ("반기순이익", 25)):
            collected.loc[
                (collected["period"] == "H1")
                & (collected["account_nm"] == account),
                "thstrm_add_amount",
            ] = amount
        collected.to_csv(source, index=False)
        from_official_cumulative = analyze(self.root).set_index("period")
        self.assertEqual(from_official_cumulative.loc["H1", "revenue"], 650)
        self.assertEqual(from_official_cumulative.loc["H1", "net_income"], 25)

    def test_incremental_collection_preserves_older_statement_history(self) -> None:
        statements = pd.DataFrame([{
            "year": 2024, "period": "FY", "period_order": 4,
            "category": "annual", "report_code": "11011", "fs_div": "CFS",
            "sj_div": "BS", "account_id": "ifrs_Assets", "account_nm": "자산총계",
            "thstrm_amount": 1000, "thstrm_add_amount": None,
            "thstrm_nm": "2024년", "currency": "KRW",
        }])
        statements.to_csv(self.root / "data" / "financial_statements.csv", index=False)
        pd.DataFrame([{
            "year": 2024, "period": "FY", "period_order": 4,
            "category": "annual", "report_code": "11011", "fs_div": "CFS",
            "status": "saved", "accounts": 1,
        }]).to_csv(self.root / "data" / "reports.csv", index=False)

        summary = collect(self.root, FakeDartClient(), now_year=2026)
        self.assertEqual(summary, {"saved": 2, "missing": 6})
        refreshed = pd.read_csv(self.root / "data" / "financial_statements.csv")
        self.assertEqual(
            sorted(refreshed["year"].astype(int).unique()), [2024, 2025, 2026]
        )


if __name__ == "__main__":
    unittest.main()

