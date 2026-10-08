# 논문 그림 자동 캡처, MANOVA 값 표시, 0.2.0 세 번째 빌드

## 날짜
2026-10-08

## MANOVA 표의 값 표시

MANOVA 탭은 통계량 값을 항상 `.6e`(유효숫자 일곱 자리, 예: `2.467366e-02`)로 표시했다. 열이 좁아
값이 `2....`처럼 잘렸고, F 근사가 담보하지 않는 정밀도를 내세웠다. 저자 요청으로 `.3e`(예:
`2.467e-02`)로 바꿨다(`components/widgets/analysis_info.py`). 자유도·F·p는 그대로. 테스트
`test_manova_value_has_four_significant_figures` — 이전 코드에서는 실패.

## 논문 그림: `scripts/paper_figures/`

논문(Chapter 2) Figure 2–6의 화면을 Windows에서 손으로 찍던 것을 WSL에서 자동으로 찍게 했다.
`run_all.sh <checkout> <tardigrades.zip> <out>`이 임시 HOME에 그림 전용 라이브러리를 만들고
(tardigrade 이미지 + Rovinsky et al. 2021 공개본 206개), 개인 Xvfb 화면에서 Modan2를 띄워
사용자가 하듯 조작한다 — 데이터셋 선택, 대화상자 입력, 분석 실행, 형태공간에서 표본 클릭, 곡선 추적.

| 스크립트 | 그림 |
|---|---|
| `fig2_3.py` | 2a, 2c, 2d, 3a(General 탭), 3b, 3c(=2b), 3d |
| `fig4_5.py` | 4a–d, 5a, 5b |
| `fig6cd.py` | 6c–d (결측 landmark가 있는 표본) |
| `fig6ab.py` | 6b 몸 외곽을 따라 세 번 클릭해 추적(semi-landmark 8개), 맞춤 끔/켬; 6a 그 결과의 곡선 설정 |

데스크톱과 다르게 처리해야 했던 것:

- **모달 대화상자**(`exec_()`)는 열기 전에 건 타이머로 조작한다.
- **형상 격자**는 플롯 위에 겹친 반투명 최상위 창이라, compositor가 없는 Xvfb에서는 투명 부분이 검게
  나온다. 각 뷰의 framebuffer를 알파째(`grabFrameBuffer(withAlpha=True)`) 창 grab 위에 직접 그린다.
- **마우스 이동**: `QTest.mouseMove`는 실제 커서를 움직이는데 Xvfb에서는 그 motion 이벤트가 다음
  클릭보다 늦게 와서, 곡선 점이 하나씩 밀렸다(첫 점 두 번, 마지막 점 누락). 이동 이벤트를 뷰어에 직접 보낸다.
- **트리 선택**: `select` 뒤에 `setCurrentIndex`를 또 부르면 개체 표가 비었다. `setCurrentIndex` 하나로
  선택하고, 그래도 비면 `load_object`.
- **리소스 경로**: `mu.resource_path`가 cwd 기준이라 체크아웃을 cwd로 실행해야 migration이 돈다.

tardigrade 이미지는 공개 자료가 아니라 저자 라이브러리에서 JSON+ZIP으로 내보낸 패키지를 받는다
(`export_dataset.py`). 곡선이 있는 원래 Figure 6 자료는 어느 DB에도 없어 새로 추적했다.

## 0.2.0 세 번째 빌드

0.2.0은 오늘 두 번 배포됐다(build 908, 이어서 922 — 868d20f). 논문의 수치와 그림은 v0.2.0으로 낸다고
쓰는데, 그 둘은 build 908의 코드(5173275)로 만들어져 있었고, 그림에는 위 MANOVA 표시가 필요하다.
저자 결정으로 v0.2.0 태그와 릴리스를 지우고 이 변경을 포함한 커밋에서 다시 만든다. CHANGELOG의
[0.2.0] 절은 이 빌드가 908과 922를 대체한다고 쓰고, Changed에 MANOVA 표시를 넣었다. 논문의
벤치마크와 그림은 새 태그에서 다시 만든다.
