from __future__ import annotations

import io
import os
import zipfile
from typing import Any
from xml.etree import ElementTree

import requests


BASE_URL = "https://opendart.fss.or.kr/api"
API_KEY_ENV = "OPENDART_API_KEY"
LEGACY_API_KEY_ENV = "DART_API_KEY"
NO_DATA_STATUS = "013"


class DartAPIError(RuntimeError):
    def __init__(self, message: str, *, status: str | None = None) -> None:
        super().__init__(message)
        self.status = status


class DartClient:
    def __init__(self, api_key: str, timeout: int = 60) -> None:
        if not api_key:
            raise ValueError(
                f"{API_KEY_ENV} 환경변수가 비어 있습니다. GitHub Actions Secret을 확인하세요."
            )
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    @classmethod
    def from_environment(cls) -> "DartClient":
        return cls(
            os.environ.get(API_KEY_ENV)
            or os.environ.get(LEGACY_API_KEY_ENV, "")
        )

    def _get(self, endpoint: str, **params: str) -> requests.Response:
        response = self.session.get(
            f"{BASE_URL}/{endpoint}",
            params={"crtfc_key": self.api_key, **params},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def _get_json(self, endpoint: str, **params: str) -> dict[str, Any]:
        payload = self._get(endpoint, **params).json()
        status = payload.get("status")
        if status != "000":
            raise DartAPIError(
                f"OpenDART 오류 status={status}: {payload.get('message', '알 수 없는 오류')}",
                status=status,
            )
        return payload

    def corporation_codes(self) -> list[dict[str, str]]:
        with zipfile.ZipFile(io.BytesIO(self._get("corpCode.xml").content)) as archive:
            xml_name = next(
                name for name in archive.namelist() if name.lower().endswith(".xml")
            )
            root = ElementTree.fromstring(archive.read(xml_name))
        return [
            {child.tag: (child.text or "").strip() for child in item}
            for item in root.findall("list")
        ]

    def corp_code_for_stock(self, stock_code: str) -> str:
        for item in self.corporation_codes():
            if item.get("stock_code", "").zfill(6) == stock_code.zfill(6):
                return item["corp_code"]
        raise DartAPIError(f"종목코드 {stock_code}의 DART 고유번호를 찾지 못했습니다.")

    def financial_statement(
        self,
        corp_code: str,
        business_year: int,
        report_code: str,
        fs_div: str,
    ) -> dict[str, Any]:
        return self._get_json(
            "fnlttSinglAcntAll.json",
            corp_code=corp_code,
            bsns_year=str(business_year),
            reprt_code=report_code,
            fs_div=fs_div,
        )

