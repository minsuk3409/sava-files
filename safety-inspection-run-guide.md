# 현장 안전보건 점검관리 시제품 실행 방법

별도 시제품이며 기존 weather-monitoring 저장소는 변경하지 않습니다.

## 파일 준비

실행 코드는 이 저장소의 `safety-inspection/` 폴더에 함께 저장되어 있습니다.

```sh
git clone https://github.com/minsuk3409/sava-files.git
cd sava-files/safety-inspection
```

## 실행
Python 3.12 이상에서:

```sh
# 위에서 이동한 safety-inspection 폴더에서 실행
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

로컬 포트 3100에서 실행합니다. 현재 서버는 검증용 루프백 바인딩이며 외부 공개 URL은 배포하지 않았습니다.

## 범위
- XLSX/HWPX/텍스트 PDF에서 원문 위치와 텍스트 추출
- 현장명, 점검일별 보고서 등록
- 사람이 확인한 지적사항의 위험도/담당자/완료기한/조치상태 저장
- 현장별 통계 및 필터
- SQLite 영속 저장: data/inspection.db

외부 AI, 문서분석 API에 데이터를 전송하지 않습니다. 업로드한 원본 바이너리는 보관하지 않으며, 추출된 텍스트와 입력 결과는 로컬 DB에 저장됩니다. DB에도 민감정보가 들어갈 수 있습니다. 가상 문서로만 검증하세요. 사내 보안 문서를 외부로 업로드하거나 보안을 해제할 필요가 없습니다.

자동 지적사항 판독, OCR, 여러 원본을 하나의 점검으로 묶는 기능, 차트, 기존 안전플랫폼 연동은 아직 구현하지 않았습니다. 보고서 수 중복을 피하려면 점검당 대표 파일 하나를 등록하세요.

## 사내 적용 전 필요한 작업
회사 승인 배포 환경, SSO/인증, 현장별 권한, 감사로그, 보관/삭제 정책, HTTPS, 파일검사, 운영 서버와 백업 구성이 필요합니다. 현재 서버는 사내 운영 또는 인터넷 공개용이 아닙니다. 승인된 사내 환경에서 보고서 양식을 검토하고 추출 규칙을 검증합니다. 보안 정책 우회를 위한 문서 변환/복사/업로드는 하지 않습니다.

## 공개 데모 배포

예정 주소: https://minsuk3409.github.io/sava-files/

`docs/index.html`은 가상 데이터 전용 데모입니다. 실제 파일 업로드나 서버 저장은 지원하지 않습니다. Python 서버는 GitHub Pages에서 실행되지 않습니다.

GitHub 저장소 Settings → Pages → Build and deployment → Source를 **GitHub Actions**로 설정합니다. 이후 Actions의 **Publish safety inspection demo** 워크플로를 실행합니다. 배포 작업이 성공한 후 위 주소에서 확인할 수 있습니다. 주소 존재만으로 배포 완료를 의미하지 않습니다.

로컬 서버를 실행한 컴퓨터에서는 브라우저 주소창에 `http://127.0.0.1:3100`을 입력합니다. 사내 운영 배포 전에는 회사 승인 및 인증/권한 구현이 필요합니다.

## Vercel 자동 배포 (공개 데모)

1. Vercel에 로그인한 뒤 **Add New → Project**에서 GitHub 저장소 `minsuk3409/sava-files`를 가져옵니다. 저장소가 보이지 않으면 Vercel GitHub 앱의 해당 저장소 접근을 허용합니다.
2. **Root Directory**는 저장소 루트(`.`)로 유지합니다. `vercel.json`에서 Framework 없음, 빌드 명령 `node scripts/build-demo.mjs`, 출력 폴더 `dist`를 설정했습니다. 환경변수나 API 키는 필요하지 않습니다.
3. **Deploy**를 실행합니다. 프로젝트 Settings → Environments 또는 Git의 Production Branch가 `main`인지 확인합니다.
4. 이후 `main`에 push하면 운영 배포가 자동 갱신됩니다. PR/다른 브랜치에는 Vercel 설정에 따라 미리보기 배포가 생성됩니다.
5. Vercel이 발급한 실제 도메인에서 가상 보고서 3건, 현장 2개, 미완료 지적 2건이 표시되는지 확인합니다. 배포 도메인은 Vercel 프로젝트 화면에서 확인합니다.

이 배포는 `docs/`의 가상 데이터 데모만 제공합니다. `safety-inspection/app.py`의 문서 업로드·DB 서버는 실행되지 않으며, 파일 업로드도 차단되어 있습니다. 인증된 사내 문서 분석 서비스를 배포하려면 별도의 운영 구성과 회사 승인이 필요합니다.

GitHub Pages 배포는 별도 워크플로입니다. Vercel Git 연동 자동 배포는 GitHub Pages 설정 활성화 여부와 관계없이 동작합니다. Vercel 연결에는 계정에서 최초 1회의 GitHub 저장소 연결/프로젝트 생성이 필요하며, 토큰을 문서나 채팅에 입력하지 않습니다.

### Vercel 배포 성공인데 404가 나오는 경우

빌드 로그에 `Public demo built: .../dist/index.html (... bytes)`가 나오는지 확인합니다. 이 메시지가 없다면 최신 커밋 배포인지 확인합니다.
프로젝트 Settings → Build and Deployment에서 Root Directory는 저장소 루트로 설정하고, Build Command/Output Directory의 프로젝트별 Override는 해제하여 `vercel.json`을 사용합니다. Production Branch는 `main`입니다.
배포 상세 화면의 생성된 Deployment URL에서도 404인지 확인합니다. Deployment URL이 정상이고 대표 도메인만 404이면 Domains에서 해당 도메인이 이 프로젝트의 Production 배포에 연결되어 있는지 확인합니다.
