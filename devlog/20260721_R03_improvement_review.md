# R03 — 개선점 리뷰 (2026-07-21 세션)

**Date:** 2026-07-21
**Type:** review (R) — 0.1.8 릴리스 직후 개선점 정리
**Related:** devlog 220–225, `TODOs.md`

0.1.8 작업(WSL OOM 수사, 첨부 시점 다운스케일+원본 보관, 추정 회전 정합,
다이얼로그 수명주기 누수 수정) 과정에서 드러난 개선점들. 우선순위 순.

---

## 1. 이미지 교체 시 고아 파일 (실질 버그) — HIGH

`MdObject.update_image`(`MdModel.py:393`)는 기존 `MdImage` **DB 행만** 지우고
새 행을 만든다. 파일 경로가 `<storage>/<ds.id>/<obj.id>.<확장자>`라서 새
이미지의 확장자가 같으면 덮어쓰지만, **다르면 이전 작업본이 디스크에 고아로
남는다**. 첨부 시점 다운스케일(devlog 222) 도입으로 `originals/` 보관본까지
고아가 될 수 있어 시급도가 올라갔다.

- 수정: `update_image`에서 새 파일을 쓰기 전에 이전 이미지의
  `get_file_path()` / `get_original_file_path()`를 삭제 (실패는 warning으로
  무시 — 교체 자체를 막지 않는다).
- 3D 모델은 교체 경로가 없어(`save_object`가 `not has_threed_model()`일 때만
  `add_threed_model`) 해당 없음.
- 관련 별건: 데이터셋 삭제 시 `<storage>/<ds.id>/` 디렉터리가 통째로 고아가
  되는 문제도 있다 (row만 삭제). 함께 정리 검토.

## 2. 표시용 추정 vs 분석용 대입 이원화 — MEDIUM (통계 영향)

다이얼로그의 "show estimate"는 회전 포함 similarity 정합(devlog 221)으로
고쳤지만, 분석 파이프라인의
`MdModel.procrustes_superimposition_with_imputation`은 여전히 정렬 공간에서
평균형 좌표 단순 대입이다. 화면에 보이는 추정과 분석에 들어가는 값이 다를 수
있다. 통일이 정도(正道)이나 **분석 결과가 바뀌는 변경**이므로 실데이터 검증
시간을 확보한 뒤 별도 작업으로.

## 3. 픽스맵 스케일링 품질 — MEDIUM (저비용)

`ObjectViewer2D`의 `scaled()` 호출이 모두 기본(고속 nearest-neighbor) 변환.
`Qt.SmoothTransformation` 적용 시 특히 Show Original 상태의 줌 화질이 눈에
띄게 개선된다. 단 24MP 원본에서는 휠 틱마다 풀 리샘플이라 비용이 커지므로,
Show Original 성능 피드백과 함께 조정할 것.

## 4. 한국어 번역 갱신 — MEDIUM

"Show Original" 등 0.1.8 신규 문구가 ts/qm에 없다. lupdate → 번역 → lrelease
한 사이클 필요 (`Modan2_ko.ts` / `Modan2_ko.qm`).

## 5. CLAUDE.md / 코드 인덱스 최신화 — LOW (위생)

CLAUDE.md가 버전 0.1.4, 존재하지 않는 `ModanDialogs.py`(6,511줄) 구조, 테스트
500개(실제 1,428개) 등 낡은 정보를 담고 있어 이후 세션을 오도한다. `.index/`
도 마찬가지일 것 (`python tools/build_index.py`).

## 6. skipped 테스트 75개 점검 — LOW

환경 제약(GUI 마커)이면 정상이나, 잊힌 채 썩는 스킵이 섞여 있는지 한 번
분류해 둘 것.

## 7. 기존 TODOs.md MEDIUM/LOW 백로그 — LOW

magic sentinel(±99999), in-method import, `enumerate` 전환, builtin shadowing
등. 급하지 않음 (TODOs.md 참조).
