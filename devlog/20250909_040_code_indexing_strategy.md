# 코드 인덱싱 및 구조화 전략

소스코드를 매번 처음부터 읽지 않고도 효율적으로 탐색/질의할 수 있도록, 코드 → 구조화 메타데이터 → 인덱스 파이프라인을 설계하는 방법입니다.

---

## 1. 인덱스 3층 구조
1. **레벨 A: 어휘/기호 인덱스**
   - 목적: 심볼 정의/참조 위치 즉시 검색
   - 도구: universal-ctags, ripgrep, 언어별 LSP
   - 산출: 정의-참조 맵, import 그래프

2. **레벨 B: AST/그래프 인덱스**
   - 목적: 호출 그래프, 의존 그래프, 클래스/상속 관계
   - 도구: tree-sitter, pycg, jdeps 등
   - 산출: 함수/클래스 카드(시그니처, 호출자/피호출자)

3. **레벨 C: 임베딩/요약 인덱스**
   - 목적: 자연어 질의 ↔ 코드 심볼 매핑
   - 전략: 함수/클래스 단위 청크, 메타데이터 태깅, 벡터DB 구축
   - 산출: 벡터DB + 심볼 메타데이터 JSON

---

## 2. 심볼 카드 예시
```json
{
  "symbol": "modan2.viewer.overlay.draw_landmarks",
  "kind": "function",
  "lang": "python",
  "file": "modan2/viewer/overlay.py",
  "signature": "draw_landmarks(points: np.ndarray, labels: bool=True) -> None",
  "doc": "Draw 3D landmarks and optional index labels on the OpenGL overlay.",
  "calls": ["opengl.draw_points", "opengl.draw_text3d"],
  "called_by": ["viewer.render_frame"],
  "imports": ["numpy as np", "PyOpenGL.GL"],
  "tests": ["tests/test_overlay.py::test_draw_landmarks"]
}
```

---

## 3. 인덱싱 파이프라인
1. **스캐너 단계**: 파일 목록 수집 → 정의/참조 정보 추출
2. **파서/그래프 단계**: AST 파싱, 호출/의존 그래프 생성
3. **품질/보안 메타데이터**: 린트/타입체커, 보안 스캐너 결과 병합
4. **요약/임베딩 단계**: 심볼 요약 생성, 임베딩 후 벡터DB에 업서트
5. **증분 업데이트**: Git diff 기반 변경된 심볼만 재생성

---

## 4. 질의 워크플로우
- 질의 → 벡터 검색(심볼 카드) → 정의/참조/호출 정보 보강 → 필요한 코드 스니펫만 첨부
- 원본 전체 파일 로딩 불필요

---

## 5. GitHub Actions 예시
1. 이벤트: push, pull_request
2. 단계:
   - 환경 세팅
   - `make index` 실행
   - 산출물 업로드: ctags.json, cards/*.json, vector.faiss
3. PR 코멘트: 변경된 심볼 및 영향 범위 보고

---

## 6. 에디터 통합
- LSP 프록시로 심볼 카드 요약을 hover/definition에 주입
- 검색 패널: 심볼 카드 기반 탐색
- 배지: 테스트/보안/오너/커밋 시간 등 표시

---

## 7. 파이썬/Qt/OpenGL 레포 적용
- 타입/린트: pyright, ruff, bandit
- 호출 그래프: pycg
- 문서: pdoc/sphinx
- OpenGL 렌더 경로는 서브그래프로 카드화

---

## 8. 폴더 구조 예시
```
code_index/
  a_index/ctags.json
  b_graph/callgraph.json
  cards/
    modan2.viewer.overlay.draw_landmarks.json
  embeddings/
    index.faiss
    meta.sqlite
tools/
  build_index.py
  gen_cards.py
  embed_cards.py
```

---

## 9. 핵심 팁
- 청크 기준은 함수/클래스
- 요약 캐싱으로 비용 절약
- 메타데이터 필터링으로 검색 정확도 향상
- 테스트 ↔ 심볼 연결 유지
