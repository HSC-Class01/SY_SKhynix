from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
METRIC_COLUMNS = (
    "revenue", "operating_income", "net_income", "assets", "liabilities",
    "equity", "current_assets", "current_liabilities", "cash_and_equivalents",
    "borrowings", "operating_cash_flow", "capex", "free_cash_flow", "net_debt",
    "operating_margin_pct", "net_margin_pct", "debt_to_equity_pct",
    "current_ratio_pct", "equity_ratio_pct", "roa_pct", "roe_pct",
)
OUTPUT_COLUMNS = (
    "year", "period", "period_order", "category", "report_code", "fs_div",
    *METRIC_COLUMNS,
)

ACCOUNT_ALIASES = {
    "revenue": ("매출액", "수익(매출액)", "영업수익"),
    "operating_income": ("영업이익", "영업이익(손실)"),
    "net_income": (
        "당기순이익", "당기순이익(손실)", "반기순이익", "반기순손실",
        "분기순이익", "분기순손실",
    ),
    "assets": ("자산총계",),
    "liabilities": ("부채총계",),
    "equity": ("자본총계",),
    "current_assets": ("유동자산",),
    "current_liabilities": ("유동부채",),
    "cash_and_equivalents": ("현금및현금성자산",),
    "borrowings": ("단기차입금", "장기차입금"),
    "operating_cash_flow": ("영업활동현금흐름", "영업활동으로인한현금흐름"),
    "capex": (
        "유형자산의취득", "유형자산의 취득", "유형자산 취득",
        "유형자산의증가", "유형자산의 증가",
    ),
}


def _normalized(value: object) -> str:
    return "".join(str(value or "").split())


def _number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    cleaned = str(value).replace(",", "").strip()
    if cleaned in {"", "-", "nan"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _amount(
    group: pd.DataFrame,
    aliases: tuple[str, ...],
    *,
    statement: tuple[str, ...] | None = None,
    sum_matches: bool = False,
) -> float | None:
    names = {_normalized(alias) for alias in aliases}
    selected = group
    if statement and "sj_div" in group.columns and group["sj_div"].isin(statement).any():
        selected = group[group["sj_div"].isin(statement)]
    matches = selected[selected["account_nm"].map(_normalized).isin(names)]
    values = [_number(value) for value in matches["thstrm_amount"]]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) if sum_matches else values[0]


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator * 100, 2)


def analyze(root: Path = ROOT) -> pd.DataFrame:
    source = root / "data" / "financial_statements.csv"
    output = root / "data" / "metrics.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists() or source.stat().st_size == 0:
        empty = pd.DataFrame(columns=OUTPUT_COLUMNS)
        empty.to_csv(output, index=False)
        return empty

    frame = pd.read_csv(source, dtype={"report_code": str})
    if frame.empty:
        empty = pd.DataFrame(columns=OUTPUT_COLUMNS)
        empty.to_csv(output, index=False)
        return empty

    rows: list[dict[str, Any]] = []
    statement_for = {
        "revenue": ("IS", "CIS"), "operating_income": ("IS", "CIS"),
        "net_income": ("IS", "CIS"), "assets": ("BS",),
        "liabilities": ("BS",), "equity": ("BS",), "current_assets": ("BS",),
        "current_liabilities": ("BS",), "cash_and_equivalents": ("BS",),
        "borrowings": ("BS",), "operating_cash_flow": ("CF",), "capex": ("CF",),
    }
    group_columns = [
        "year", "period", "period_order", "category", "report_code", "fs_div"
    ]
    for keys, group in frame.groupby(group_columns, dropna=False):
        base = dict(zip(group_columns, keys))
        values = {
            name: _amount(
                group,
                aliases,
                statement=statement_for[name],
                sum_matches=name == "borrowings",
            )
            for name, aliases in ACCOUNT_ALIASES.items()
        }
        # OpenDART reports Q3 income and cash-flow amounts year-to-date. Convert
        # them to the standalone third quarter by removing H1 cumulative values.
        if base["period"] == "Q3":
            prior = frame[
                (frame["year"] == base["year"])
                & (frame["period"] == "H1")
                & (frame["fs_div"] == base["fs_div"])
            ]
            for name in ("revenue", "operating_income", "net_income", "operating_cash_flow", "capex"):
                prior_value = _amount(
                    prior,
                    ACCOUNT_ALIASES[name],
                    statement=statement_for[name],
                ) if not prior.empty else None
                if values[name] is not None and prior_value is not None:
                    values[name] -= prior_value
        capex = values["capex"]
        cfo = values["operating_cash_flow"]
        free_cash_flow = (
            cfo - abs(capex) if cfo is not None and capex is not None else None
        )
        cash = values["cash_and_equivalents"]
        borrowings = values["borrowings"]
        net_debt = (
            borrowings - cash
            if borrowings is not None and cash is not None
            else None
        )
        rows.append(
            {
                **base,
                **values,
                "free_cash_flow": free_cash_flow,
                "net_debt": net_debt,
                "operating_margin_pct": _ratio(
                    values["operating_income"], values["revenue"]
                ),
                "net_margin_pct": _ratio(values["net_income"], values["revenue"]),
                "debt_to_equity_pct": _ratio(values["liabilities"], values["equity"]),
                "current_ratio_pct": _ratio(
                    values["current_assets"], values["current_liabilities"]
                ),
                "equity_ratio_pct": _ratio(values["equity"], values["assets"]),
                "roa_pct": _ratio(values["net_income"], values["assets"]),
                "roe_pct": _ratio(values["net_income"], values["equity"]),
            }
        )

    result = pd.DataFrame(rows, columns=OUTPUT_COLUMNS).sort_values(
        ["year", "period_order"]
    )
    result.to_csv(output, index=False)
    print(json.dumps({"metrics": len(result), "output": str(output)}, ensure_ascii=False))
    return result


if __name__ == "__main__":
    analyze()

