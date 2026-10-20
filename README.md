[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97%20%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-2563eb?style=for-the-badge)](https://hsc-class01.github.io/SY_SKhynix/)

# SK하이닉스 OpenDART 재무 대시보드

OpenDART 구조화 재무제표를 수집해 SK하이닉스의 연간·반기·분기 재무 수치와 비율을 분석합니다.

## 🔗 대시보드 바로가기

[https://hsc-class01.github.io/SY_SKhynix/](https://hsc-class01.github.io/SY_SKhynix/)

## 대시보드 구성

- 상단: 최근 공시 핵심 지표와 연도별 매출·이익, 수익성·재무안정성 그래프
- 하단: Annual, Half-year, Quarterly 세 종류의 상세 재무 표
- 재무 수치: 매출액, 영업이익, 당기순이익, 자산·부채·자본, 유동자산·부채, 현금, 차입금, 영업현금흐름, 유형자산 취득, 잉여현금흐름, 순차입금
- 재무비율: 영업이익률, 순이익률, 부채비율, 유동비율, 자기자본비율, ROA, ROE
- 최하단: 국내 비교기업(Peer firms) 표

## OpenDART API 설정

1. [OpenDART](https://opendart.fss.or.kr/)에서 인증키를 발급합니다.
2. GitHub 저장소의 **Settings → Secrets and variables → Actions → New repository secret**으로 이동합니다.
3. Secret 이름을 `OPENDART_API_KEY`로 하고 발급 키를 값으로 저장합니다. 기존 `DART_API_KEY` Secret도 호환됩니다.
4. **Actions → SK hynix DART dashboard → Run workflow**로 최초 수집·배포를 실행합니다.

인증키는 Python 코드, `config.json`, README 또는 공개 파일에 직접 넣지 마세요. 로컬 실행 시에는 환경변수로 입력합니다.

```powershell
python -m pip install -r requirements.txt
$env:OPENDART_API_KEY = "발급받은_OpenDART_인증키"
python -m src.collect
python -m src.analyze
python -m src.dashboard
python -m http.server 8000
```

브라우저에서 `http://localhost:8000`을 여세요. 저장소의 매월 자동 실행과 배포에는 Repository Secret이 필요합니다.

## 자동 갱신

`.github/workflows/update.yml`이 매월 1일 00:15 UTC(한국시간 09:15)에 OpenDART 데이터를 수집하고, 분석 파일과 대시보드 데이터를 저장소에 반영합니다. `workflow_dispatch`를 통해 수동 실행도 할 수 있습니다. GitHub Actions의 일정 실행은 혼잡 시 지연될 수 있습니다.

## 데이터 정의와 해석

금액 원자료는 원(KRW) 단위로 보존하고 화면에서는 억원으로 표시합니다. 연결재무제표(CFS)를 우선 사용하고 해당 보고서가 없으면 별도재무제표(OFS)를 조회합니다. 사업보고서(FY), 반기보고서(H1), 1분기(Q1), 3분기(Q3)를 수집합니다. 분기보고서 손익·현금흐름 누적치는 반기 누적액을 차감해 Q3 단독값으로 계산합니다. 자산·부채·자본은 기간말 잔액입니다. ROA·ROE는 평균잔액이 아닌 기간말 잔액을 이용합니다. 해당 보고서/계정이 없으면 0으로 대체하지 않고 빈 값으로 둡니다.

## 국내 Peer firms

| 기업 | 종목코드 | 관계 | 비교 관점 |
|---|---:|---|---|
| 삼성전자 | 005930 | 직접 비교기업 | 국내 메모리·종합반도체 대형 IDM |
| 한미반도체 | 042700 | HBM 공급망 | HBM 패키징·후공정 장비 투자 사이클 |
| 하나마이크론 | 067310 | 메모리 후공정 | 패키징·테스트 사업과 메모리 수요 |
| SFA반도체 | 036540 | 메모리 후공정 | 패키징·테스트 사업과 가동률 |
| DB하이텍 | 000990 | 인접 비교기업 | 국내 반도체 제조업 재무구조 (파운드리, 사업구조 상이) |

삼성전자만 메모리 IDM 직접 비교 대상으로 보고, 나머지는 HBM·후공정 공급망 또는 인접 반도체 기업으로 구분합니다. 사업 구조 차이가 있으므로 단순 비율 비교는 참고용입니다.

## Agent 개발용 ZIP

저장소 루트의 `SY_SKhynix_DART_Agent.zip`에서 프로젝트 파일과 API 입력 안내를 내려받을 수 있습니다. ZIP에는 숨김 파일과 `.github` 디렉터리를 넣지 않았습니다. 자동화 파일은 ZIP의 `github_workflows/update.yml`에서 제공하며, 저장소 적용 시 `.github/workflows/update.yml`에 위치해야 합니다.

## 주요 경로

- `src/collect.py`, `src/dart_client.py`: OpenDART 수집
- `src/analyze.py`: 계정 정리 및 비율 계산
- `src/dashboard.py`, `index.html`, `app.js`, `styles.css`: 대시보드
- `data/financial_statements.csv`, `data/metrics.csv`, `data/reports.csv`: 수집·분석 자료
- `data/peers.csv`: 국내 peer firms
- `github_workflows/update.yml`: 숨김 파일 없는 ZIP용 워크플로 사본

분석 결과는 공시 기반 참고자료이며 투자 조언이 아닙니다.

