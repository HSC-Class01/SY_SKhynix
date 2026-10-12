import os
import io
import zipfile
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

API_KEY = os.environ.get("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"

if not API_KEY:
    raise RuntimeError("DART_API_KEY 인증키가 설정되지 않았습니다.")

def get_corp_code():
    response = requests.get(
        f"{BASE_URL}/corpCode.xml",
        params={"crtfc_key": API_KEY},
        timeout=60,
    )
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        xml_file = next(
            name for name in archive.namelist()
            if name.lower().endswith(".xml")
        )
        root = ET.fromstring(archive.read(xml_file))

    for item in root.findall("list"):
        name = (item.findtext("corp_name") or "").strip()
        if name == "SK하이닉스":
            return item.findtext("corp_code")

    raise RuntimeError("DART 기업 목록에서 SK하이닉스를 찾지 못했습니다.")

def get_financial_data(corp_code):
    rows = []
    current_year = datetime.now().year

    for year in range(2010, current_year):
        params = {
            "crtfc_key": API_KEY,
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": "11011",
            "fs_div": "CFS",
        }

        response = requests.get(
            f"{BASE_URL}/fnlttSinglAcntAll.json",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status") != "000":
            print(f"{year}년 데이터 없음 또는 조회 실패: "
                  f"{result.get('message', '')}")
            continue

        for item in result.get("list", []):
            rows.append({
                "year": year,
                "company": "SK하이닉스",
                "statement": item.get("sj_nm"),
                "account": item.get("account_nm"),
                "account_id": item.get("account_id"),
                "current_amount": item.get("thstrm_amount"),
                "previous_amount": item.get("frmtrm_amount"),
                "currency": item.get("currency"),
            })

        print(f"{year}년 조회 완료")

    return rows

def main():
    corp_code = get_corp_code()
    print("SK하이닉스 기업코드:", corp_code)

    rows = get_financial_data(corp_code)
    if not rows:
        raise RuntimeError(
            "재무 데이터가 없습니다. API 응답과 인증키를 확인하세요."
        )

    output = Path("data")
    output.mkdir(parents=True, exist_ok=True)

    file_path = output / "sk_hynix_financials.csv"
    pd.DataFrame(rows).to_csv(
        file_path, index=False, encoding="utf-8-sig"
    )

    print(f"저장 완료: {file_path} ({len(rows)}개 항목)")

if __name__ == "__main__":
    main()
