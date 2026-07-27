# ruff G 도입, PTH는 근거를 남기고 보류

## 날짜
2026-07-27

## 배경

R05 단계적 도입의 마지막 두 그룹. 둘 다 위반 수가 크다 — G 256건, PTH 322건 —
그러나 성격이 정반대여서 결론도 갈렸다.

## G (flake8-logging-format) — 도입

256건 중 **252건이 G004**(로깅 호출의 f-string)다. 사실상 이 프로젝트의 로깅
스타일 전체다.

G004의 논거는 "레벨이 꺼져 있어도 문자열이 즉시 포매팅된다"는 것이다. 맞는
지적이지만, 이 정도 로깅 양의 데스크톱 앱에서 그 절약은 측정되지 않는 수준이고,
지연 형식은 읽기 어려운 데다 인자 순서를 바꿀 때 틀리기 쉽다:

```python
logger.info(f"Imported {n} objects from {path}")          # 현재
logger.info("Imported %s objects from %s", n, path)       # G004가 요구하는 형태
```

252곳을 후자로 바꾸는 것은 침습적이고 얻는 게 적다. **G004는 근거와 함께 무시**하고
그룹은 활성화했다.

남은 **G201 4건은 진짜 개선**이었다 — `except` 블록 안의
`logger.error(..., exc_info=True)` 는 `logger.exception(...)` 이 정확한 표현이다
(`MdHelpers.py:53`, `data_exploration_dialog.py:901`,
`dataset_analysis_dialog.py:689`, `main.py:287`). 넷 다 변환.

즉 이 그룹은 **노이즈 252 : 실제 문제 4** 였고, 노이즈를 끄고 나머지를 남기는 것이
정확한 처리다.

## PTH (flake8-use-pathlib) — 보류

322건: 앱 118, 테스트 189, 도구 18.

### 왜 지금 하지 않는가

서브룰이 두 종류로 갈린다.

**(1) 술어/동작 규칙 — 안전.** bool을 반환하거나 제자리에서 동작하므로 경계를
넘는 값이 없다: PTH110 exists(62), PTH103 makedirs(11), PTH107/108
remove/unlink(24), PTH112 isdir(5), PTH116 stat(2), PTH202 getsize(5),
PTH104/105 rename/replace(2), PTH208 listdir(3).

**(2) 값 생성 규칙 — 위험.** PTH120 dirname(88), PTH100 abspath(43),
PTH118 join(26), PTH119 basename, PTH122 splitext, PTH111 expanduser,
PTH123 open(41).

문제는 이것이다:

```python
def get_file_path(self, base_path=mu.DEFAULT_STORAGE_DIRECTORY):
    return os.path.join(base_path, str(...id), str(...id) + "." + ext)   # -> str
```

이 반환값은 `shutil` 호출, `open()`, 문자열 비교, JSON+ZIP의 경로 처리, DB 필드로
흘러간다. `Path` 를 반환하게 되면 일부는 즉시 터지지만(JSON 직렬화 등),

```python
Path("a/b") != "a/b"   # True
```

**비교가 조용히 어긋나는 부류가 더 위험하다.** 저장된 문자열과 대조하는 코드가
아무 오류 없이 매칭에 실패한다.

### 판단

바로 오늘, 같은 세션에서 `\bobject\b` 일괄 치환이 `self.object` 속성까지 바꿔
세그폴트를 냈다(devlog 267). 그때는 전체 스위트가 잡아냈지만, 위 부류는 **조용히
틀리는** 실패 모드라 테스트가 잡아준다는 보장이 약하다.

322건을 서둘러 반쯤 처리하는 것보다, **분석과 순서를 남기고 다음에 제대로 하는 것**
이 맞다고 판단했다. `TODOs.md` 에 위 분류와 함께 권장 순서를 적었다: 술어 규칙 먼저
(기계적이고 스위트로 검증 가능) → 값 규칙은 함수 단위로, 호출부를 확인하며.
**이 그룹은 일괄 자동수정하지 말 것.**

## 검증

`ruff check .` / `ruff format .` 클린. 관련 테스트 374 passed, 1 skipped.

## 현황

```
E F I N UP B C4 LOG RUF012 S DTZ C901(래칫 19) PIE RET SIM PERF A G   ← 적용
PTH                                                                  ← 보류(계획 기록됨)
```

근거와 함께 무시 중인 서브룰: S110/S112/S311, RET504, SIM102, SIM108, G004.
