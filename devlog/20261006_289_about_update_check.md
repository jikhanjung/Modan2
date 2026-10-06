# About 창의 새 버전 확인

## 날짜
2026-10-06

## 무엇
Help → About(F1)을 열면 GitHub 릴리스 목록을 확인해, 새 버전이 있으면 실행 중인
OS용 설치 파일 링크와 릴리스 노트 링크를 보여준다. 자동 다운로드·설치는 하지
않는다. 네트워크 접속은 About을 열 때만, 세션당 한 번(`MdUpdate.py`,
`ModanMainWindow._start_update_check`).

## 어떤 릴리스를 "새 버전"으로 볼까
지금까지의 0.2.0 빌드는 전부 pre-release라 GitHub `/releases/latest`(pre-release
제외)는 쓸 수 없다. 목록 전체를 받아 직접 고른다.

- 정식 릴리스: 실행 중인 버전보다 높으면 항상 제안.
- pre-release: **같은 major.minor.patch 줄**이고 실행 중인 버전도 pre-release일
  때만. 0.2.0-beta.5 사용자에게 0.2.0-beta.6·0.2.0-rc.1·0.2.0은 제안하지만
  0.3.0-alpha.1(EFA 테스트 빌드, devlog 288)은 제안하지 않는다.
- 정식 릴리스 사용자에게는 정식 릴리스만. 그래서 지금 0.1.12 사용자는 0.2.0
  베타를 안내받지 못하고 "최신 버전" 문구를 본다 — 0.2.0 정식이 나오면 해소된다.
  이 점이 문제가 되면 규칙을 조정할 것.
- draft와 semver가 아닌 태그는 무시.

자산 선택: Windows `*Windows-Installer*.zip`(없으면 다른 Windows zip), macOS
`.dmg`, Linux `.AppImage`. 해당 OS 파일이 없으면 릴리스 페이지로 링크.

## 인증서 — 연구소 네트워크
처음에는 certifi 번들만 썼다(고정 macOS 빌드의 OpenSSL이 시스템 인증서를 못
찾는 문제 대비). 그러나 KOPRI처럼 TLS를 검사하는 네트워크는 연구소 루트
인증서로 다시 서명하고, 그 루트는 **OS 저장소에만** 있다. certifi만 쓰면 오히려
연구소 안에서 실패한다. 그래서 순서를:

1. `truststore` — OS 기본 검증기(Windows 인증서 저장소, macOS 키체인, Linux 배포판
   CA 파일). 연구소 루트를 인식.
2. `certifi` — 시스템 인증서를 못 찾는 고정 빌드용 예비.

로 두고, **인증서 검증 실패일 때만** 다음 것으로 넘어간다(네트워크 단절·타임아웃은
즉시 실패). 모든 컨텍스트가 검증을 한다(테스트로 고정) — 검증을 끄는 폴백은 없다.
프록시는 urllib이 환경변수와 Windows 시스템 설정에서 찾는다(PAC 스크립트는 미지원).

**연구소 안에서의 실제 동작은 아직 검증하지 않았다** — 사용자가 직접 테스트 예정.

의존성 추가: `truststore`(MIT), `certifi`(MPL-2.0, CA 번들 무수정 배포).
THIRD-PARTY-NOTICES에 반영. PyInstaller는 빌드 시 설치되는 hooks-contrib의 certifi
훅으로 `cacert.pem`을 번들한다. truststore는 순수 Python.

## 스레드
QThread가 아니라 daemon `threading.Thread` + 큐 신호(`_UpdateCheckSignals`). 느린
네트워크가 About 창을 막거나, 종료 시 실행 중인 QThread가 프로세스를 abort시키는
일을 피하기 위해서다. 결과가 오면 열려 있는 About 창의 문구를 바꾼다.

## 테스트
`tests/test_update_check.py`: 제안 규칙(11가지 조합), 플랫폼별 자산, draft·비semver
태그 무시, 자산 없을 때 페이지 링크, 인증서 실패 시에만 다음 신뢰 소스로 재시도,
모든 컨텍스트가 검증함, About 문구와 도착 시 갱신, 세션당 1회, 오프라인 보고.
`conftest.py`의 autouse 픽스처가 `fetch_releases`를 실패시켜 **테스트는 네트워크에
나가지 않는다**(기존 About 테스트들이 실제로 창을 연다).

실제 GitHub 응답으로 수동 확인: 0.2.0-beta.3 → beta.5 설치 파일(3개 OS 각각),
0.2.0-beta.5·0.3.0-alpha.1 → 제안 없음.

## 번역·문서
UI 문자열 8개를 `Modan2_ko.ts`에 직접 추가(밀린 다른 문자열은 건드리지 않음,
devlog 288 참고), `.qm` 재생성. 사용자 가이드 "Checking for Updates" 절과 한국어
`.po`, CHANGELOG `[Unreleased]` Added.
