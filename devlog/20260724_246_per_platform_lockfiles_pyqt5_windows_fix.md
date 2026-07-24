# Lockfile 수정: universal → per-platform (PyQt5 Windows 빌드 실패)

## 날짜
2026-07-24

## 배경

[[20260724_244_ci_lockfiles_codeql_version_test]]에서 도입한 **universal
hashed lockfile**(`requirements.lock` / `requirements-dev.lock`)이 push 후
자동 트리거된 Build 워크플로의 **Windows job에서 설치 실패**했다.

```
ERROR: Could not find a version that satisfies the requirement pyqt5-qt5==5.15.19
       (from versions: 5.15.2)
ERROR: No matching distribution found for pyqt5-qt5==5.15.19
```

## 근본 원인

`PyQt5-Qt5`(PyQt5의 Qt 바이너리 의존성)는 **플랫폼마다 최신 버전이 다르다**:
- Linux/macOS: 5.15.19까지 존재
- **Windows: 5.15.2가 마지막** (이후 wheel을 안 냄)

`uv pip compile --universal`은 전 플랫폼 공통 단일 핀을 뽑으려다 5.15.19를
선택했는데, Windows엔 그 버전 wheel이 없어 `--require-hashes` 설치가 깨졌다.
이전에는 `pip install pyqt5`(느슨한 요구사항)가 플랫폼별로 알아서 골라 문제가
없었던 것. **PyQt5 앱에서는 universal 단일 lock이 성립하지 않는다.**

## 수정: per-platform lockfile

universal 2개 파일을 플랫폼별 3개로 교체:

| 파일 | pyqt5-qt5 | pkgs |
|---|---|---|
| `requirements-linux.lock` | 5.15.19 | 48 |
| `requirements-windows.lock` | **5.15.2** | 49 |
| `requirements-macos.lock` | 5.15.19 | 48 |

- 각 파일은 full set(런타임 + dev/test, `requirements.txt` +
  `config/requirements-dev.txt`), hash-pin, 3.11 floor(테스트 매트릭스 3.11·3.12
  커버). 빌드 job이 test 의존성까지 설치하지만 PyInstaller가 미사용 패키지를
  번들하지 않으므로 산출물엔 무영향 — 오히려 "빌드가 테스트와 동일한 런타임
  해상도"라는 보장이 강해진다.
- 생성: `uv pip compile requirements.txt config/requirements-dev.txt
  --python-platform {linux,windows,macos} --python-version 3.11 --generate-hashes`.
  (`--universal` 제거, `--python-platform` 사용.)

### 검증한 것
- `--python-platform windows` → `pyqt5-qt5==5.15.2` 정확히 선택(핵심 수정).
- **macOS arm64 확인**: `macos-latest`가 Apple Silicon이라, uv의 `macos` alias가
  `aarch64-apple-darwin`을 타깃하는지 검증 → 일치. 게다가 arm64/x86_64 lock이
  byte-identical(uv가 두 mac 아키텍처 hash를 모두 포함) → 두 아키텍처 모두 커버.
- `pip install --require-hashes --dry-run -r requirements-linux.lock` → 통과.
- `pip-audit -r requirements-linux.lock` → 48 pkg, 취약점 0.

## 워크플로/도구 반영
- **`test.yml`**: `$RUNNER_OS`로 lock 선택(Linux/Windows/macOS). 캐시 키
  `hashFiles('requirements-*.lock')`.
- **`reusable_build.yml`**: 3개 빌드 job이 각자 OS lock 설치
  (windows/macos/linux).
- **`security.yml`**: pip-audit → `requirements-linux.lock`(ubuntu 러너), lock-check
  잡은 `make lock-check`가 3개 전부 검사.
- **`Makefile`**: `lock`/`lock-check`가 `PLATFORMS := linux windows macos`를 순회.
- **문서**: `config/README.md`, `CLAUDE.md`의 lockfile 설명 갱신.

## 교훈
- `--universal` lock은 편리하지만, **플랫폼별로 릴리스 지점이 갈리는 바이너리
  의존성(PyQt5-Qt5)**이 있으면 성립하지 않는다. GUI(PyQt/PySide) 프로젝트는
  per-platform lock이 사실상 표준.
- 로컬(Linux)에서만 검증했던 244의 lock이 **다른 플랫폼에서 처음 CI로 드러난**
  케이스. 244의 "universal 단일 파일" payoff 문구는 이 devlog로 정정된다.

## 남은 후속
- 다음 Build/Test 실행에서 Windows·macOS 레그가 lock 설치를 통과하는지 확인
  (Linux는 로컬 검증 완료, Windows/macOS는 CI가 첫 실검증).
- 244의 패키징 스모크 스텝(devlog 245)도 같은 실행에서 함께 관찰.
