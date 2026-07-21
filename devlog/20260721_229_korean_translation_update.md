# 한국어 번역 갱신 (R03 항목 4)

## 날짜
2026-07-21

## 배경

0.1.8까지 추가된 문구들("Show Original" 등)이 번역 파일에 없어 한국어 UI에
영어가 섞여 나왔다. 실제로 확인해 보니 이번 세션 추가분뿐 아니라 그 이전에
쌓인 미번역이 훨씬 많았다.

## 작업

### 1. 문자열 추출

`Modan2.py` 하단 docstring에 적힌 절차대로 `pylupdate5` 실행. 다만 소스 목록은
현재 구조에 맞게 `tr()`/`QCoreApplication.translate` 호출이 실제로 있는 13개
파일로 잡았다 (`ModanComponents.py`는 이제 shim이라 실체는 `components/` 아래):

```
Modan2.py components/viewers/object_viewer_2d.py components/widgets/analysis_info.py
components/widgets/table_view.py dialogs/*.py
```

결과: 메시지 237개 → 290개, 미번역 54개.

### 2. 번역

54개를 기존 용어에 맞춰 번역했다 (데이터셋 / 개체 / 랜드마크 / 분석 / 범례 /
가져오기 / 내보내기). 주요 신규 문구:

| 원문 | 번역 |
|---|---|
| Show Original | 원본 보기 |
| Show Estimated | 추정값 보기 |
| Add Missing / Insert Missing | 결측 추가 / 결측 삽입 |
| Missing landmarks | 결측 랜드마크 |
| Performing Procrustes superimposition... | 프로크루스테스 중첩을 수행하는 중... |
| Include image and model files | 이미지 및 모델 파일 포함 |
| Var. explained | 설명된 분산 |

`{}`, `{e}`, `{}/{}` 같은 자리표시자는 개수와 순서를 기계적으로 검증해가며
채웠다 — 파이썬 `str.format`은 위치 기반이라 순서가 바뀌면 런타임에 깨진다.
그래서 예를 들어 "Found {} coordinate(s) with the value {}."는 개수→값 순서를
유지해 "{}개의 좌표에서 값 {}을(를) 찾았습니다."로 옮겼다.

### 3. 함정: `type="unfinished"`인데 번역문이 있는 항목

`pylupdate5`는 같은 원문이 다른 context에 이미 번역돼 있으면 그 번역을
복사해 오면서도 `type="unfinished"` 플래그를 남긴다. **lrelease는 unfinished
항목을 .qm에 넣지 않으므로** 이 상태면 번역문이 있어도 화면엔 영어가 나온다.
해당 4건('범례', '정보', '경고', '닫기')의 플래그를 제거했다.

### 4. 컴파일

이 환경엔 `lrelease`/`lconvert` 래퍼만 있고 실제 바이너리가 없어
(`qttools5-dev-tools` 미설치, sudo 불가) `qt5-applications` 휠을 임시
디렉터리에 풀어 그 안의 `lrelease`를 사용했다 — 사용자 venv는 건드리지 않음.

```
lrelease translations/Modan2_ko.ts   # 276 finished, 0 unfinished
```

`QTranslator`로 실제 로딩과 번역 결과를 확인했다 (신규 문구 12개 표본 검증).

## 하지 않은 것

- **`translations/Modan2_en.ts`**: 173개 중 171개가 빈 번역이다. 영어는 원문이
  곧 번역이라 빈 항목이 그대로 원문으로 폴백되므로 동작이 이미 정확하다.
  재생성해도 동작 변화 없이 diff만 커져서 두었다.

## 루트의 낡은 번역 파일 삭제

메시지 1개짜리 잔재로, 코드·빌드(`build.py`, `Modan2.spec`)·인스톨러 어디서도
참조하지 않았다 (실제 로딩 경로는 `translations/Modan2_ko.qm`). 실수로 이쪽을
고치고 왜 반영이 안 되는지 헤맬 수 있는 함정이라 삭제했다. devlog 172에서도
같은 파일을 "never used"로 짚은 적이 있다.

## 다음에 번역을 갱신할 때

1. `pylupdate5 <위 13개 파일> -ts translations/Modan2_ko.ts`
2. 새로 생긴 `<translation type="unfinished"></translation>` 채우기
3. **번역문이 있는데 `type="unfinished"`인 항목의 플래그 제거** (3번 항목)
4. `lrelease translations/Modan2_ko.ts`
5. `QTranslator`로 표본 검증
