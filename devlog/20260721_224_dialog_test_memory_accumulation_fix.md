# 다이얼로그 테스트 메모리 누적 수정 (DeferredDelete 미전달)

## 날짜
2026-07-21

## 문제 (TODOs.md "Test infra" 항목)

전체 스위트 RSS가 ~800MB까지 단조 증가하며 돌아오지 않았고, 증가분 대부분이
다이얼로그 계열 테스트 파일이었다 (`test_data_exploration_scatter.py` +110MB,
`test_export_dialog.py` +69MB, `test_preferences_dialog.py` +58MB,
`test_dataset_analysis_scatter.py` +53MB 등).

## 조사

테스트마다 RSS와 함께 살아있는 Qt 객체 수를 기록하는 진단 플러그인으로 측정:

- gc 기준 파이썬 쪽 QDialog/FigureCanvas 참조는 **0** — 파이썬 누수가 아님.
- 반면 `QApplication.allWidgets()`는 테스트당 +34~125개씩 단조 증가, 4개 파일
  후 위젯 5,291개 / 톱레벨 150개 잔존. **위젯이 Qt(C++) 쪽에서 삭제되지 않고
  쌓이는 것**이 원인.

메커니즘: pytest-qt의 `qtbot.addWidget`은 테스트 teardown에서 `close()` +
`deleteLater()`를 호출하지만, Qt의 `DeferredDelete` 이벤트는 **이벤트 루프
복귀 또는 명시적 `sendPostedEvents(None, QEvent.DeferredDelete)`로만 전달**되고
일반 `processEvents()`는 이를 건너뛴다. 테스트 사이에는 이벤트 루프가 돌지
않으므로 qtbot에 등록된 모든 위젯 트리가 세션 끝까지 삭제 대기 상태로
살아남았다. 다이얼로그 하나에 `Figure(figsize=(20,16), dpi=100)` 캔버스
(2000×1600 Agg 버퍼 ≈ 12.8MB)가 2~3개씩 붙어 있어 파일당 수십 MB가 쌓였다.

증거: 우연히 이벤트 루프성 경로를 타는 `test_okay_button_click`에서만 위젯이
5291→91로 떨어졌고, 그 이후 해당 파일의 테스트당 증가가 1.9MB→0.2MB로
떨어졌다 (RSS 자체는 glibc arena 반환 문제로 감소하지 않지만 성장이 멈춤).

## 수정 (`tests/conftest.py`)

`pytest_runtest_logfinish` 훅 추가 — logfinish는 teardown 단계(pytest-qt의
위젯 close/deleteLater 포함) **이후**에 실행되므로 이 시점에 삭제가 전부
대기 중이다:

```python
for _ in range(3):  # 삭제가 또 다른 삭제를 예약할 수 있음
    app.sendPostedEvents(None, QEvent.DeferredDelete)
    app.processEvents()
gc.collect(0)
```

처음에는 full `gc.collect()`를 썼으나 대형 힙에서 테스트당 수십 ms가 쌓여
스위트 실행 시간이 약 2배(128s→328s)가 됐다. 방금 만들어진 matplotlib
Figure/canvas 순환 참조는 young generation에 있으므로 `gc.collect(0)`로
충분하고, 이 경우 메모리 효과는 동일하면서 오히려 기존보다 빨라졌다
(4개 파일 기준 39s→26s — 위젯을 제때 지우니 이벤트 처리가 가벼워짐).

## 결과

- 매 테스트 종료 시 잔존 위젯 **0개** (이전: 단조 증가).
- 문제의 4개 파일: 종료 RSS 579MB → 399MB, 테스트당 증가 15~46MB → <1MB.
- 전체 스위트 피크 RSS: **825MB → 531MB** (1428 passed, 75 skipped).
- 남은 파일별 증가분(dataset_analysis_scatter +57MB 등)은 대부분 1회성 모듈
  로딩(openpyxl 등)과 glibc의 RSS 미반환으로, 누적 성장은 멈췄다.

## 참고

- 이미 해제된 메모리의 RSS 미반환(glibc arena)은 별개 현상으로, 성장이 멈춘
  이상 실질 문제가 아니다.
- 진단 방법(위젯 카운트 플러그인)은 재사용 가치가 있어 여기 기록해 둠:
  per-test로 `QApplication.allWidgets()` 개수와 VmRSS를 같이 찍으면
  "파이썬 참조 누수 vs Qt 삭제 미처리 vs 단순 RSS 미반환"이 바로 구분된다.
