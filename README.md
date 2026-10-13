# SK하이닉스 DART 재무 대시보드

OpenDART에서 수집한 SK하이닉스 연결 재무제표 데이터를 기반으로 연도별 주요 재무 항목과 비율을 표시합니다.

## 대시보드
- GitHub Pages: https://hsc-class01.github.io/SY_SKhynix/
- 원자료: `data/sk_hynix_financials.csv`
- 수집 스크립트: `dart_api.py`
- 자동 업데이트: `.github/workflows/update.yml` (매월 1일 UTC 00:00 및 수동 실행)

## 표시 항목
- 매출액, 영업이익, 당기순이익, 자산총계
- 연도별 매출액·영업이익 추이
- 영업이익률과 부채비율(원자료에 필요한 계정이 있는 경우)
- 연도별 주요 재무 데이터 표

## 설정 및 문제 해결
1. 저장소 Settings → Secrets and variables → Actions에서 `DART_API_KEY`를 Repository secret으로 설정합니다.
2. Actions 탭에서 **Update SK Hynix Financial Data** 워크플로를 수동 실행할 수 있습니다.
3. Settings → Pages에서 배포 방식이 **Deploy from a branch**라면 Branch `main`, Folder `/ (root)`를 선택합니다. GitHub Actions 방식으로 이미 설정되어 있다면 현재 설정을 유지하고 별도의 Pages 배포 워크플로를 구성해야 합니다.
4. Pages가 반영되지 않으면 Actions 실행 결과와 Pages 배포 상태를 확인하고 브라우저 캐시를 새로고침합니다.

## 데이터 범위와 한계
수집 스크립트는 DART API에서 2010년부터 직전 완료 연도까지 사업보고서(11011)의 연결재무제표(CFS)를 요청합니다. DART API에 없는 연도/계정은 대시보드에서 0으로 대체하지 않고 `—`로 표시합니다. 계정명은 보고서/표준계정에 따라 달라질 수 있으므로 모든 재무비율이 모든 연도에 산출되는 것은 아닙니다.

데이터는 교육·분석 참고용이며 투자 권유가 아닙니다.
