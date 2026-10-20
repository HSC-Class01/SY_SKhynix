# OpenDART API 키 및 GitHub 설정

## API 키 발급 및 등록

1. https://opendart.fss.or.kr/ 에서 OpenDART 인증키를 신청합니다.
2. 저장소 **Settings → Secrets and variables → Actions → New repository secret**을 엽니다.
3. 이름 `OPENDART_API_KEY`, 값은 발급받은 키로 저장합니다. 기존 워크플로 호환을 위해 `DART_API_KEY`도 지원합니다.
4. 키를 코드·README·일반 변수·공개 파일에 저장하지 마세요.

## 최초 수집

Actions 탭에서 **SK hynix DART dashboard → Run workflow**를 실행합니다. 워크플로는 DART에서 연결재무제표를 우선 수집하고, 결과 CSV와 대시보드 데이터를 저장소에 반영합니다.

## 대시보드 게시

저장소 Settings → Pages의 Build and deployment가 **Deploy from a branch**, Branch `main`, Folder `/(root)`인지 확인합니다. 현재 GitHub Pages 주소는 https://hsc-class01.github.io/SY_SKhynix/ 입니다. main 브랜치의 root `index.html`, `styles.css`, `app.js`, `dashboard-data.js`를 Pages가 제공합니다.

## 수동 로컬 실행

```powershell
python -m pip install -r requirements.txt
$env:OPENDART_API_KEY = "발급받은_OpenDART_인증키"
python -m src.collect
python -m src.analyze
python -m src.dashboard
python -m http.server 8000
```

이후 http://localhost:8000 을 엽니다. 키를 로컬에서 입력할 때는 PowerShell 세션 환경변수로 설정합니다.

## 월간 자동 갱신

`.github/workflows/update.yml`은 매월 1일 00:15 UTC, 한국시간 09:15에 실행됩니다. GitHub 일정 실행은 혼잡할 때 늦어질 수 있습니다. Actions 탭에서 언제든 수동 실행도 가능합니다.
