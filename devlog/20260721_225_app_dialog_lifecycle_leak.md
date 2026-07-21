# 앱 다이얼로그 수명주기 누수 수정 (닫힌 다이얼로그가 삭제되지 않던 문제)

## 날짜
2026-07-21

## 문제

devlog 224의 테스트 인프라 조사에서 파생된 실사용 누수. 코드베이스 어디에도
`WA_DeleteOnClose`가 없고 모든 다이얼로그가 메인 윈도우를 부모로 생성되는데,
Qt에서 부모 있는 다이얼로그는 닫아도 **숨겨질 뿐 부모가 소유한 채 잔존**한다.
게다가 `self.exploration_dialog = DataExplorationDialog(self)`처럼 열 때마다
속성을 새 인스턴스로 덮어써도, 이전 인스턴스는 C++ 쪽에서 메인 윈도우의
자식으로 계속 살아있다.

결과: 데이터 탐색 창을 10번 열면 숨겨진 `DataExplorationDialog` 10개(각각
2000×1600 matplotlib 캔버스 2~3개, 캔버스당 ~13MB + GL 뷰어)가 앱 종료까지
잔존 — 장시간 사용 시 메모리가 계속 불어난다.

## 수정 (`Modan2.py`)

두 가지 패턴으로 모든 다이얼로그 생성 지점을 정리:

1. **`show()` 비모달** — `DatasetAnalysisDialog`(1곳),
   `DataExplorationDialog`(2곳): 생성 직후 `setAttribute(Qt.WA_DeleteOnClose)`.
   닫히는 즉시 삭제된다. 속성은 다이얼로그 클래스가 아니라 **호출부에서**
   설정 — 테스트가 다이얼로그를 직접 만들 때 pytest-qt teardown(close 후
   deleteLater)과 충돌하지 않게 하기 위함.

2. **`exec_()` 모달** — Preferences / NewAnalysis / Import(2곳) / Export /
   DatasetDialog(2곳) / ObjectDialog(2곳) / ProgressDialog(2곳): exec 반환
   직후 `deleteLater()`. DeferredDelete는 슬롯이 이벤트 루프로 복귀한 뒤
   처리되므로, `ret`이나 `self.dlg.object_deleted`처럼 exec 이후 같은 슬롯
   안에서 속성을 읽는 코드는 안전하다.

3. **댕글링 가드** — 닫힌(=삭제된) 다이얼로그를 만질 수 있는 유일한 지점인
   메인 윈도우 `closeEvent`의 `self.analysis_dialog.close()`를
   `try/except RuntimeError`로 감쌌다 (sip 래퍼는 C++ 객체보다 오래 산다).

## 참고

- `DataExplorationDialog`의 부모 없는 `shape_grid` 뷰들은 다이얼로그 래퍼가
  참조를 쥐고 있으므로, 다음 열기에서 속성이 재바인딩되어 래퍼가 수거될 때
  함께 해제된다 (한 세대 지연, 무한 누적 아님).
- 다이얼로그 내부에서 만드는 하위 다이얼로그(CalibrationDialog 등)는 부모
  다이얼로그가 이제 실제로 삭제되므로 함께 정리된다.
- 테스트 쪽 대응 수정은 devlog 224 (pytest-qt DeferredDelete 미전달).
