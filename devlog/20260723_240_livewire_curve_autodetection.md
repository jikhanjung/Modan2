# 곡선 자동감지 — 라이브와이어(Intelligent Scissors) 구현

## 날짜
2026-07-23

## 배경

세미랜드마크 계획([[20260722_237_semilandmark_support_plan]])의 남은 TODO 중
"곡선 자동 감지(live-wire)"를 구현했다. 기존 곡선 트레이스는 사용자가 곡선 위의
점을 하나하나 클릭해야 했고, 그 위에 편집·관리 UI가
[[20260722_238_curve_editing_ui]]에서 얹혔다. 라이브와이어는 클릭 사이 구간을
**이미지의 가장 강한 에지에 스냅**해서, 완만한 윤곽은 시작점·끝점만으로, 크게
휘는 윤곽은 시작·중간·끝 정도만으로 트레이스가 되도록 한다.

기법은 Mortensen & Barrett 1995 "Intelligent Scissors for Image Composition"의
최소비용 경로 접근을 따른다.

## 설계

### 데이터 흐름
`MdLiveWire.py` (신규 모듈) — 순수 numpy/scipy, GUI 무관, 독립 테스트 가능하게
두 조각으로 분리:

1. **비용장** `compute_cost_field(gray)` — 그레이스케일 이미지를 픽셀별 이동
   비용으로 변환. Sobel gradient 크기가 큰(강한 에지) 픽셀은 비용이 낮고
   (`_MIN_COST`≈1e-3), 평탄 영역은 높다(≈1). 최소비용 경로가 자연히 경계선을
   껴안는다.
2. **최소경로 스냅** `LiveWire` — 비용장에서 8-연결 격자 그래프를 한 번 만들고,
   seed(첫 클릭)에서 Dijkstra를 1회 돌려 predecessor 맵을 캐시한다. 이후 커서가
   움직일 때마다 `path_to(target)`는 그 맵을 역추적만 하므로 O(경로길이)로 싸다
   (실시간 미리보기 가능).
3. `build_livewire(gray, max_dim=1024)` — 위 둘을 묶고, 큰 이미지는 정수 배율로
   다운스케일해 그래프를 감당 가능하게 유지하되, 외부에는 여전히 원해상도
   `(x, y)` 좌표로 말한다(내부에서 scale로 나눴다 곱해 복원).

### gradient 방향 항 (곡선 추종의 핵심)
비용장(gradient 크기)만으로는 경로가 에지 "위"에 있으려 할 뿐, 에지 방향을
매끄럽게 이어갈 유인이 없어 실제 사진(질감·노이즈)에서 흔들리거나 가로지를 수
있다. 그래서 Mortensen-Barrett의 **link 방향 항 f_D**를 엣지 가중치에 추가:

- 각 픽셀의 **에지 접선** = gradient를 90° 회전한 단위벡터 `(gy, -gx)/|g|`.
- 엣지 p→q의 f_D는 링크 방향이 양 끝점의 접선과 얼마나 정렬됐는지로 `[0,1]`
  (정렬=0, 가로지름→1).
- 최종 가중치 = `(_W_MAGNITUDE·비용[q] + _W_DIRECTION·f_D) · 이동거리`
  (현재 0.6/0.4; Laplacian 항은 생략하고 둘을 재정규화).

이 항 덕분에 경로가 에지 접선을 따라 흘러 **가로지르기를 억제**한다.

### 실측
반원(크게 휘는 곡선) 합성 이미지에서 **시작점·끝점 2개만으로** 트레이스:
- 노이즈 없음: 경로가 실제 원호를 평균 |dist-r| **0.29px**(최대 0.95px)로 추종.
- 노이즈 σ=60(대비의 ~25%): 평균 **0.35px**로 유지(방향 항의 강건성).
지름(chord)으로 가로지르지 않고 x가 중심+반지름까지 부풀어 호를 탄다. 닫힌
윤곽의 좌/우 두 경로 모호성은 중간점 클릭으로 해소된다.

## GUI 통합 (2D 뷰어)

`components/viewers/object_viewer_2d.py`:
- 상태: `livewire_enabled`, `_livewire`(캐시), `livewire_preview`.
- `set_livewire_enabled(on)` 토글, `_reset_livewire()`(이미지 변경 시),
  `_pixmap_to_gray()`(QPixmap→uint8 2D), `_ensure_livewire()`(orig_pixmap에서
  지연 빌드·캐시), `_livewire_segment(a,b)`(스냅 경로, 이미지 없으면 직선 폴백).
- 좌표계: 비용장은 orig_pixmap 픽셀 공간 = 트레이스 점의 이미지 좌표 공간
  (`_2imgx`/`_2imgy`)과 동일 → 추가 변환 불필요.
- EDIT_CURVE 클릭: snap 켜져 있고 앞선 점이 있으면, 직전 점→클릭 구간을
  라이브와이어로 스냅해 중간점들을 `current_curve_points`에 확장(그 외엔 기존대로
  단일 점 추가). 이후 `finish_curve` 흐름은 무변경.
- 마우스 이동: 스냅 미리보기 경로 계산 → paintEvent에서 점선으로 렌더.
- 곡선 확정/취소/모드 이탈/이미지 변경 시 미리보기·캐시 정리.

### accept/cancel UX
라이브와이어는 대화형이라 별도 감지-후-수락이 아니라 트레이스 완료가 곧 accept다.
발견성을 위해 키보드·상태바를 보강:
- **각 클릭** = 스냅 구간 확정(commit), **더블클릭/Enter** = 곡선 전체 accept
  (`finish_curve`→N→리샘플→append), **우클릭/Esc** = 진행 중 트레이스 취소.
- 완료/취소 로직을 `_accept_current_curve()`/`_cancel_current_curve()` 헬퍼로
  뽑아 더블클릭·우클릭과 키 입력이 공유. `keyPressEvent`에서 Enter/Esc 처리.
- QLabel은 기본 포커스를 안 받으므로 `setFocusPolicy(Qt.ClickFocus)`로 키 입력
  수신(클릭 시 포커스 획득).
- 상태바 힌트를 snap 상태에 맞춰: 켜짐 "Snap on: click along the edge;
  Enter/double-click to accept, Esc/right-click to cancel", 꺼짐도 accept/cancel
  키를 명시. `set_livewire_enabled` 토글 시 즉시 갱신.

`dialogs/object_dialog.py`:
- **"Snap to curve" 체크박스**(`cbxSnapToCurve`)를 옵션 체크박스 열에 추가.
  기본 꺼짐이며 **곡선 모드에서만 활성화**(다른 모드에선 비활성/회색). 곡선 모드
  진입 시 체크 상태를 뷰어에 적용(`_apply_snap`), 재진입해도 마지막 선택 복원.
  라이브와이어는 2D 전용이라 `set_livewire_enabled` 유무를 확인 후 전달.
  (초기엔 툴버튼 형태였다가, 발견성을 위해 제목 있는 체크박스로 교체.)

## 테스트

- `tests/test_livewire.py` (21) — 비용장(에지가 더 쌈, 범위, 예외), 최소경로
  스냅(채널 스냅·우회·seed 재사용·범위 클램프), 다운스케일 팩토리, **곡선 추종**
  (양 끝점만으로 원호 추종·노이즈 강건·중간점 방향 결정).
- `tests/test_livewire_viewer.py` (16) — QPixmap→gray, 토글/캐시 리셋,
  orig_pixmap 스냅, **Snap 체크박스 전달·곡선 모드에서만 활성·진입 시 상태 적용**,
  **Enter accept·Esc cancel**, 힌트가 snap 상태에 따라 바뀜.
- 37개 신규 전부 통과. 기존 뷰어/대화상자/세미랜드마크 스위트 회귀 없음.

## 남은 것 / 한계

- **곡선 추종 품질은 합성 이미지로만 검증**했다. 실제 표본 사진(질감·조명
  그라디언트)에서의 체감은 앱에서 직접 확인 필요. 필요 시 가중치(0.6/0.4)나
  Laplacian 영교차 항 추가로 튜닝.
- **3D 곡선 모드** 미지원(라이브와이어는 2D 전용). 다음 후보.
- 세미랜드마크 계획의 다른 잔여 항목(정렬 중 슬라이딩, 가중치)은 여전히 범위 밖
  (기록만 유지, [[20260722_237_semilandmark_support_plan]] 참조).

## 관련 커밋
- `3a3d969` feat: Live-wire curve auto-detection (intelligent scissors)
- `37fcbbc` test: End-to-end analysis on semi-landmark datasets
