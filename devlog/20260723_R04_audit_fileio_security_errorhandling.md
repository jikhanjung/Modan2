# R04 — 파일 I/O · 보안 · 에러 처리 감사 (2026-07-23 세션)

**Date:** 2026-07-23
**Type:** review (R) — 0.2.0-alpha.1 태깅 직후 소스 전반 취약점 점검
**Related:** devlog 234(인코딩 startup 버그), commit `31b49f7`(리더 비-ASCII 이름 대응),
semi-landmark 커브 기능(devlog 237–240)
**Scope:** 애플리케이션 코드 전체(`tests/` 제외). 세 축으로 병렬 감사 —
파일 I/O·인코딩 견고성 / 보안 취약점 / 에러 처리·리소스 관리.

발단: "아까 파일오픈 같은 문제 없는지, 그 외 취약점도" 점검 요청. `31b49f7`에서
고친 인코딩 버그가 다른 경로에 남아있는지 확인하는 것이 출발점이었고, 실제로
남아있었다(#1). 아래는 우선순위 순. 각 항목 실제 코드로 검증 완료.

> **상태 표기:** ☐ 미착수 · ◐ 진행 · ☑ 완료.
> **2026-07-23 갱신: #1~#14 전부 수정 완료.** 하단 [적용 결과](#적용-결과) 참고.
> 회귀 테스트: `1745 passed, 8 skipped` (신규 회귀 테스트 5건 추가).

---

## 🔴 HIGH — 실질 버그, 우선 수정

### 1. 인코딩 버그가 "쌍둥이 리더"에 그대로 잔존 ☐

`components/formats/`의 리더들은 `_encoding.open_text()`(bytes→utf-8-sig→locale→
latin-1 폴백)로 고쳐졌으나, **`MdUtils.py`의 병렬 리더 3종은 여전히 strict
`encoding="utf-8"`**:

- `MdUtils.py:368` `read_landmark_file`(.txt 포맷 감지)
- `MdUtils.py:398` `read_tps_file`
- `MdUtils.py:462` `read_nts_file`

이 경로는 실사용된다: `ModanController.py:367`에서 `.tps/.nts/.txt`를 데이터셋에
추가할 때 `mu.read_landmark_file()` 호출. cp949 등 비-ASCII 표본명 파일이
`UnicodeDecodeError`로 임포트 실패 — **`31b49f7`에서 고친 것과 동일 클래스의
다른 경로**. strict utf-8은 BOM도 안 벗겨 `first_line.startswith("LM=")` 포맷
감지(368–370)도 깨진다.

- **수정:** 세 리더 모두 `components.formats._encoding.open_text()`로 라우팅.

### 2. CVA/MANOVA 실패가 "성공"으로 보고됨 ☐

`ModanController.py:828–834`, `855–856` (`run_analysis` 내부):

```python
except Exception as e:
    self.logger.warning(f"CVA analysis failed: {e}")
    ...
```

PCA + 그룹핑 분석에서 CVA/MANOVA 브랜치가 실패하면 `warning` 로그만 남기고
그대로 진행 → `analysis_completed.emit(analysis)` + `info_message.emit("...
completed successfully")`(880–881). `cva_result`/`manova_result`는 `None`으로
영속화된다. **사용자는 그룹 분석을 요청했으나 결과 없이 "성공" 메시지만** 본다.

- **수정:** 실패 시 `warning_occurred`/`error_occurred`로 사용자에게 표면화
  (분석 자체는 PCA 결과로 완료하되, CVA/MANOVA 실패를 명시).

### 3. `save_object`만 트랜잭션·에러 처리 부재 ☐

`ModanController.py:539–584`:

```python
obj.save()                       # 574 — 오브젝트 행 커밋
if image_path is not None:
    if not obj.has_image():
        obj.add_image(image_path).save()   # 파일 I/O; 예외 가능
...
```

다른 모든 mutating 컨트롤러 메서드(`create/update/delete_dataset`,
`import_objects`, `_import_*`)는 `with gDatabase.atomic()` + `try/except →
error_occurred`로 감싸는데 **이 메서드만 둘 다 없다**. `add_image` /
`add_threed_model`이 574 이후 예외를 던지면 오브젝트 행은 이미 커밋, 미디어는
누락된 **반쪽 상태**로 남고, 예외는 unguarded 다이얼로그 호출부
(`ObjectDialog.Okay`)로 전파되어 앱을 크래시시킨다(→ #7).

- **수정:** 행 저장 + 미디어 첨부를 `with gDatabase.atomic()` + `try/except`로
  감싸 형제 메서드와 동일한 패턴 적용.

---

## 🟡 MEDIUM

### 4. 경로 탈출 — 악성 데이터셋 zip 임포트 ☐

`MdUtils.py:899`, `913` (`import_dataset_from_zip`의 미디어 복사):

```python
src = Path(root) / img_meta["path"]   # path는 zip 내 dataset.json에서 옴(비신뢰)
if src.exists():
    shutil.copy2(str(src), str(new_fp))
```

`dataset.json`의 `path` 필드를 봉쇄 검사 없이 `Path(root)/path`로 조인 →
`../../../../etc/passwd` 같은 값이 `root`를 탈출, `shutil.copy2`로 **임의 호스트
파일을 데이터셋에 복사**(로컬 파일 읽기/유출 후 재-export로 새어나갈 수 있음).
`safe_extract_zip`(785)의 가드는 *추출 시점*의 멤버 경로만 검사하므로 JSON
`path` 필드를 쓰는 이 복사 단계는 우회된다.

- **심각도:** Medium — 코드 실행 아님, 악성 패키지 임포트가 전제. 로컬 파일
  읽기/유출.
- **수정:** 복사 전 `src.resolve()`가 `root` 안에 있는지 확인
  (`safe_extract_zip`과 동일한 봉쇄 검사).

### 5. Object 다이얼로그 Save/Next/Prev 슬롯 unguarded + `int()` 파싱 ☐

`dialogs/object_dialog.py:1863(Okay)`, `1785(Previous)`, `1825(Next)` — 모두
`save_object()` 호출인데 `@guard_slot` 미적용. 내부 `object_dialog.py:1701`:

```python
sequence=int(self.edtSequence.text()),
```

sequence 필드가 비었거나 숫자가 아니면 `ValueError` → **전역 excepthook 부재
(#7)로 앱 종료**. 커브용 `dataset.save()`/`object.save()`(1712–1717)도 unguarded.

- **수정:** 세 슬롯에 `@guard_slot` 적용, `int()` 전 sequence 필드 검증.

### 6. STL 로드만 try/except 없음 ☐

`MdUtils.py:240` `trimesh.load_mesh(file_name)` — 바로 아래 PLY 브랜치(256)는
friendly `ValueError`로 감싸는데 STL은 raw trimesh 예외 노출. 손상/절단된 STL
에서, 3D 뷰어 드롭 핸들러(`@guard_slot`) 밖의 호출자는 크래시.

- **수정:** PLY 브랜치와 동일하게 try/except → `ValueError` 래핑.

### 7. 전역 `sys.excepthook` 부재 (구조적) ☐

`main.py`/`Modan2.py` 어디에도 `sys.excepthook` 미설치. PyQt5에서 이벤트 루프가
호출한 슬롯의 미처리 예외는 프로세스를 중단시킨다. 완충 장치는 `guard_slot`
(`MdHelpers.py:22`)뿐인데 커버리지가 부분적(예: `Modan2.py` 16 guard_slot vs 44
`.connect(`, `object_dialog.py` 5 vs 41). guard 안 걸린 슬롯의 예외 = 하드 크래시.

- **수정:** 트레이스백 로깅 + 비치명 에러 다이얼로그를 띄우는 top-level
  `sys.excepthook`을 `guard_slot` 뒤 백스톱으로 설치.

---

## 🟢 LOW — 경계/견고성

### 8. `safe_extract_zip` zip-slip 검사가 문자열 prefix 비교 ☐

`MdUtils.py:792` `if not str(resolved).startswith(str(dest)):` — 구분자 없는 raw
prefix 검사라 형제 디렉터리(`dest=/tmp/ab`, 멤버 `/tmp/abcd/…`)가 통과. 실제
`dest`는 매번 랜덤 `mkdtemp`라 실익은 낮으나 로직 오류.
- **수정:** `os.path.commonpath` 또는 `Path.is_relative_to`(3.9+)로 봉쇄 비교.

### 9. `process_3d_file` 변환 OBJ를 temp 밖에 기록 ☐

`MdUtils.py:232–234` `file_name_only = os.path.splitext(file_name)[0]`가 절대
소스 경로를 유지 → `os.path.join(temp_dir, file_name_only + ".obj")`에서 절대
두 번째 인자가 이겨 `temp_dir`이 무시되고 변환본이 **원본 옆에** 기록됨.
사용자 선택 경로라 익스플로잇은 아니고 예상치 못한 쓰기(정합성 버그).
- **수정:** `os.path.basename(file_name)` 사용.

### 10. NTS 리더 `NameError` (헤더에 row-name 마커 없을 때) ☐

`components/formats/nts.py:137` `elif len(row_names_list) > 0:` — `row_names_list`
는 122행(별도 라인 분기)에서만 바인딩. `b`/`e`/`l` 플래그가 전혀 없는 헤더는
137행에서 미바인딩 → `NameError`(기본 이름 `else`로 못 감). `guard_slot`이
잡지만 파싱 실패.
- **수정:** `read()` 상단에서 `row_names_list = []` 초기화.

### 11. X1Y1 리더 빈/짧은 파일 가드 없음 ☐

`components/formats/x1y1.py:81–83` `header = lines[0]...` → `xyz_header_list[2]` —
빈 파일은 `lines[0]`에서 `IndexError`, 3열 미만 헤더는 `[2]`에서 `IndexError`.
`guard_slot`이 잡으나 "empty/malformed" 대신 generic 에러.
- **수정:** `if not lines: return` 가드 추가.

### 12. Morphologika 리더 필수 섹션 존재 가정 ☐

`components/formats/morphologika.py:84` `raw_data[dsl].append(line)` — 섹션 헤더
이전 데이터(`dsl == ""`)에서 `KeyError`; `:98` `self.raw_data["names"]` —
`[names]` 블록 없으면 `KeyError`. `.get()`/명시 검사로 명확한 메시지.
- **수정:** `.get()` 및 섹션 존재 확인.

### 13. `objloader.py` 인코딩 없는 `open()` + 컨텍스트 매니저 없음 ☐

`objloader.py:37`, `77` `for line in open(filename):` — 활성 로더
(`OBJFileLoader.OBJ`, 3D 뷰어 671행 사용). (a) locale 기본 인코딩(비-ASCII 경로/
`usemtl` 이름 오독), (b) `float()`/`int()` 파싱 오류 시 핸들 누수(GC까지).
- **수정:** `with open(filename, encoding="utf-8", errors="replace") as fh:`.

### 14. 죽은 코드 Procrustes 변형의 0-나눗셈/빈 `raise` ☐

`MdModel.py:bookstein_registration`(1692), `resistant_fit_superimposition`(2246)
에 `1/size`(1728), `xdiff/size`(1754), `reference_distance/target_distance`(2331)
무가드 나눗셈, 그리고 `resistant_fit`의 활성 예외 없는 `raise`(2249 →
`RuntimeError: No active exception`). 모두 **모듈 밖 호출자 없음(도달 불가)**.
- **수정:** 최소 0-가드 추가 또는 죽은 코드 제거 검토.

---

## ✅ 견고하다고 확인된 부분 (조치 불필요)

- **위험한 실행:** app 코드에 `eval`/`exec`/`pickle`/`marshal`/`yaml.load`/
  비신뢰 `__import__` 없음. `subprocess`는 dev 도구(`build.py`,
  `manage_version.py`)에서 arg-list 형태로만, `shell=True`는 `docs/build_all.py`
  (dev 전용)에만.
- **역직렬화:** loaded 파일에 `pickle`/`joblib`/`numpy allow_pickle=True` 없음.
  데이터셋 패키지는 평문 `json`.
- **SQL 인젝션:** 전부 peewee ORM(파라미터화). 유일한 raw SQL은
  migrations의 `PRAGMA table_info({table})`인데 `{table}`이 하드코딩 상수.
- **XML/XXE:** app 코드에 XML 파싱 없음. TPS/NTS/X1Y1/Morphologika 모두 커스텀
  라인 기반 텍스트.
- **시크릿:** 하드코딩 자격증명/토큰/키 없음.
- **네트워크/SSRF:** download/`urlopen`/`requests` 없음. 유일한 `urlparse`는
  drag&drop `file://` URI 파싱용.
- **이미지 디컴프레션 밤:** PIL `MAX_IMAGE_PIXELS` 기본 보호 유지(미오버라이드).
- **format 리더 인코딩 코어:** `_encoding.open_text()` 견고, TPS/NTS/X1Y1/
  Morphologika 모두 사용(`tps.py:73`, `nts.py:67`, `x1y1.py:69`,
  `morphologika.py:63`).
- **이미지 로딩:** `Image.open` typed except 래핑(`MdModel.py:1004,1084–1115`),
  `QPixmap` null 체크+로깅(`object_viewer_2d.py:1774,1793`).
- **export/JSON 쓰기:** 전부 `encoding="utf-8"` 명시.
- **분석 입력 검증:** `_prepare_landmarks`(`ModanController.py:1074`)가 <2 랜드마크,
  landmark-count 불일치, 대입 불가 None을 numpy 도달 전 명확한 `ValueError`로 거부.
  `run_analysis` top-level try/except 존재(885–889).
- **신규 semi-landmark/커브 코드:** `resample_polyline`(`MdUtils.py:941`)가 <2점,
  `n<2`, `total==0`, 세그먼트 0-길이 나눗셈 가드. `get_average_shape`는 nanmean로
  ragged/NaN 안전. `rescale_to_unitsize`(1446)는 centroid size 0 가드.
- **DB 트랜잭션:** `delete_dataset`, `_import_*`, `import_dataset_from_zip`가
  `atomic()` + 롤백 시 미디어 정리(929–936) 정상.
- **미디어 파일 I/O:** `MdImage/MdThreeDModel.add_file`이 typed error 로깅+재raise
  (삼키지 않음).

---

## 종합

신규 semi-landmark 커브 기능 자체는 입력 검증·0-나눗셈 가드가 탄탄하다. 웹류
취약점(SQLi/XXE/역직렬화/시크릿)은 해당 없음이 확인됐다. 실질 우선순위는:

1. **#1** — 최근 고친 인코딩 버그가 `MdUtils.py` 쌍둥이 리더에 잔존 (요청의 발단)
2. **#2** — CVA/MANOVA 실패가 거짓 성공으로 보고
3. **#3** — `save_object` 반쪽 저장 + 크래시 전파

이번 세션에서 위 상태 표기를 갱신하며 순차 수정한다.

---

## 적용 결과

**2026-07-23, #1~#14 전부 수정 완료.** 변경 파일: `MdUtils.py`, `ModanController.py`,
`dialogs/object_dialog.py`, `components/formats/{nts,x1y1,morphologika}.py`,
`objloader.py`, `MdModel.py`, `main.py`.

| # | 항목 | 처리 |
|---|------|------|
| 1 | MdUtils 쌍둥이 리더 인코딩 | 3종 리더를 `open_text()`로 라우팅(lazy import — startup 순환/무거운 Qt 회피) |
| 2 | CVA/MANOVA 거짓 성공 | 실패를 `subordinate_failures`로 수집, `warning_occurred`로 사용자 표면화 |
| 3 | save_object 반쪽 저장 | 행 저장+미디어 첨부를 `gDatabase.atomic()`으로 래핑, 예외는 guard_slot로 전파 |
| 4 | zip 임포트 경로 탈출 | 미디어 복사 전 `_is_within_directory(root, src)` 봉쇄 검사, 위반 시 skip+warning |
| 5 | Object 슬롯 unguarded | Okay/Next/Previous에 `@guard_slot`, sequence 안전 파싱(빈 값→None) |
| 6 | STL 로드 미래핑 | PLY와 동일하게 try/except→`ValueError` |
| 7 | 전역 excepthook 부재 | `main.py`에 `_install_global_excepthook()` 백스톱(로그+비치명 다이얼로그) |
| 8 | zip-slip prefix 비교 | `_is_within_directory` 헬퍼로 경로-컴포넌트 봉쇄 비교 |
| 9 | process_3d_file 경로 | `os.path.basename()`로 temp_dir 유지 |
| 10 | NTS NameError | `row_names_list = []` 초기화 |
| 11 | X1Y1 빈/짧은 파일 | `if not lines` + 헤더 열 수 가드 → 명확한 `ValueError` |
| 12 | Morphologika 섹션 | 섹션-이전 데이터 skip + 필수 섹션(`names`/`rawpoints`) 검증 |
| 13 | objloader open() | `with open(encoding="utf-8", errors="replace")` (활성/dead 양쪽) |
| 14 | dead Procrustes | 빈 `raise`→`ValueError`, 0-나눗셈 가드 3곳 |

**신규 회귀 테스트(5):** `test_read_landmark_file_non_utf8_name_is_tolerated`(#1),
`TestPathContainment` 4건(#8/#4). 기존 `test_read_landmark_file_unicode_error`는
동작 변경(관대한 디코딩)에 맞춰 교체.

**전체 테스트:** `1745 passed, 8 skipped` — 회귀 없음. ruff check/format 통과.

### 별건 — 환경/버전 이슈 (감사와 무관, 같은 세션에서 처리)

- `datetime.UTC`(Python 3.11+ 전용) startup 크래시: 잠깐 `timezone.utc`로 우회했으나
  사용자가 **환경을 3.12로 재구성**하기로 하여 원래 `datetime.UTC`로 원복(프로젝트
  target py312·ruff UP017과 일치).
- 사용자 conda 환경의 바이너리 손상(`PyQt5.sip` 누락, `PIL._imaging` 누락) — 코드
  문제 아님. Python 3.12 새 환경 + `pip install -r requirements.txt` 재구성 권고.

### 후속 검토(선택)

- **guard_slot 커버리지 확대**: #7 백스톱이 생겼지만, 사용자 조작 슬롯 전반에
  `@guard_slot`을 넓히면 개별 컨텍스트 메시지가 더 친절해짐(구조적, 별도 작업).
  → 착수: object_dialog(Delete/입력 슬롯 4종)·data_exploration(export_chart) 가드
  추가([[20260723_241_post_audit_runtime_fixes]]). 나머지 다이얼로그 미완.
- **#4 잔여**: 봉쇄 위반은 이제 차단되나, atomic 롤백 시 복사된 미디어 orphan 파일
  정리는 import 경로의 `copied_files` cleanup에 의존 — 별도 점검 여지.
- **죽은 코드(#14) 제거**: bookstein/resistant_fit 변형은 호출자 없음 — 가드 대신
  제거도 선택지.
