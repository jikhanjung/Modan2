# 감사 후속 — 런타임 버그 수정(스캐터 축 · 한글 폰트) + 환경 진단

## 날짜
2026-07-23

## 배경

[[20260723_R04_audit_fileio_security_errorhandling]] 감사 수정을 커밋한 뒤,
사용자가 실제로 앱을 구동하며 마주친 문제들을 이어서 처리했다. 두 부류다:

1. **실제 코드 버그** — 감사 범위(파일 I/O·보안·에러 처리)에는 안 잡혔던 런타임
   크래시 2건. devlog로 남긴다.
2. **환경(설치) 문제** — 코드가 아니라 사용자 conda 환경의 손상. 진단만 기록.

## 1. 스캐터 준비에서 `axis3=None` 크래시

### 증상
Data Exploration에서 차트를 그릴 때:
```
TypeError: list indices must be integers or slices, not NoneType
  data_exploration_dialog.py:1986 in _populate_scatter_groups
    self.scatter_data[...]["z_val"].append(flip_axis3 * self.analysis_result_list[idx][axis3])
```
`update_chart`는 `@guard_slot`으로 감싸져 있어(감사 #7의 excepthook 이전에도)
앱이 죽지는 않고 에러가 표면화됐다 — guard가 제대로 동작한 사례.

### 원인
`prepare_scatter_data`는 2D/3D 여부와 무관하게 x/y/z를 **항상** 채우는데, z는
`analysis_result_list[idx][axis3]`로 인덱싱한다. `axis3 = comboAxis3.currentData()`
인데, **분석의 주성분 개수가 3 미만**이면(랜드마크가 적은 데이터셋 등)
`set_mode`의 `comboAxis3.setCurrentIndex(2)`가 존재하지 않는 인덱스라 현재 항목이
없어지고 `currentData()`가 `None`을 반환한다 → `[None]` 인덱싱에서 TypeError.

### 수정
축 값 조회를 작은 헬퍼 `axis_value(idx, axis, flip)`로 통일하고, **axis가 None
이면 평면 `0.0`으로 처리**한다. 2D 플롯은 그대로 렌더되고 3D 플롯은 평면으로
우아하게 저하한다. x1/x2/x3 세 축 모두 같은 실패 모드라 함께 방어했다.
회귀 테스트(`test_prepare_scatter_data_with_no_third_axis`)로 axis3=None 강제 →
크래시 없음, z는 0.0, x/y는 실제 PCA 점수 유지를 고정했다.

- 커밋 `6a84c3c`.

## 2. 한글 차트 텍스트가 두부(□)로 깨짐

### 증상
```
UserWarning: Glyph 48373 (\N{HANGUL SYLLABLE BOG}) missing from font(s) Times New Roman.
```
(복/사/본 … 한글 그룹명·라벨)

### 원인
`Modan2.py`의 `read_settings`가 차트 전역 폰트를
`font.family="serif"`, `font.serif=["Times New Roman"]`로 고정한다. Times New
Roman에는 한글 글리프가 없어 경고 + 두부 렌더링.

### 수정
serif 리스트에 크로스플랫폼 한글 폰트를 **폴백**으로 덧붙였다:
`["Times New Roman", "Malgun Gothic"(Win), "AppleGothic"(mac), "NanumGothic"(Linux),
"DejaVu Serif", "serif"]`. matplotlib(≥3.6)은 리스트를 **글리프별로** 순회하므로
라틴은 Times New Roman, 한글은 처음 발견되는 한글 폰트로 렌더된다. 없는 폰트명은
스킵된다. 사용자 Windows에는 Malgun Gothic이 기본 설치돼 해결.

- 주의: OS에 한글 폰트가 있어야 한다. Windows/macOS는 기본 제공, 순수 Linux는
  `fonts-nanum` 등 설치 필요. (WSL 개발 박스엔 CJK 폰트가 없어 폴백이 리스트
  끝까지 순회하는 것만 확인 가능했다.)
- 커밋 `61674d2`.

## 3. 환경(설치) 문제 — 코드 아님, 진단만

사용자 Windows conda 환경(`Modan2`)에서 앱 구동 시 연쇄 실패:

| 증상 | 원인 |
|------|------|
| `ImportError: cannot import name 'UTC' from 'datetime'` | `datetime.UTC`는 Python 3.11+ 전용 심볼. 환경이 3.10 이하. **사용자가 3.12로 재구성하기로** 하여 코드는 `datetime.UTC` 그대로 유지(프로젝트 target=py312). |
| `ModuleNotFoundError: No module named 'PyQt5.sip'` | pip PyQt5 설치본에 `sip.pyd` 바이너리 실종(깨진 설치). `--force-reinstall PyQt5 PyQt5-sip`로 해결. |
| `ImportError: cannot import name '_imaging' from 'PIL'` | Pillow C 확장 실종. 같은 바이너리 손상 계열. |

두 번째·세 번째가 같은 식으로 깨진 걸로 보아 환경 전반의 바이너리 오염.
**Python 3.12 새 conda 환경 + `pip install -r requirements.txt` 재구성**을
권고했고 사용자가 그 방향으로 진행.

## 4. 후속 — guard_slot 커버리지 확대

R04 검토거리 중 **guard_slot 커버리지 확대**를 이어서 진행했다. 위 스캐터
크래시처럼 guard가 있으면 앱을 죽이지 않고 메시지로 표면화되므로, 사용자 조작
슬롯 중 "파일/DB/파싱/numpy 작업"을 하는(= guard_slot 기준에 맞는) 미가드
슬롯을 선별해 덧붙였다. 단순 토글(show_*_state_changed 등)이나 이미 내부 경계
가드가 있는 테이블 핸들러는 제외했다.

**object_dialog.py** (주 데이터 입력 다이얼로그, 갭이 가장 큼 — 5 guarded / 41
connect):
- `Delete` — 오브젝트 DB+파일 삭제
- `btnAddInput_clicked` / `btnUpdateInput_clicked` / `btnDeleteInput_clicked` —
  좌표 입력 파싱(`float("abc")` → ValueError)·랜드마크 인덱싱

**data_exploration_dialog.py**:
- `export_chart` — 차트 파일 저장(`fig.savefig`) I/O. 나머지 combo/flip 핸들러는
  이미 가드된 `update_chart()`에 위임하거나(→ 자동 보호), `cbxShapeGrid`처럼
  try/finally로 커서를 복원하므로 제외.

회귀 테스트 `test_non_numeric_coordinate_update_is_guarded` 추가 — 비숫자 좌표로
Update 시 크래시 없이 None 반환 + 기존 랜드마크 불변을 고정. 전체 스위트
`1747 passed, 8 skipped`.

남은 후속(선택): 나머지 다이얼로그(import/export/analysis 등) 슬롯 감사,
죽은 Procrustes 변형 제거 여부([[20260723_R04_audit_fileio_security_errorhandling]]
#14), zip 임포트 롤백 시 orphan 미디어 정리(R04 #4 잔여).
