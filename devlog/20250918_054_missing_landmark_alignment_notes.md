# Missing Landmark Alignment Algorithm Notes

## 입력 조건
- `X` : `(N, K, D)` 모양의 좌표 배열 (결측은 `NaN`)
- `M` : `(N, K)` 모양의 관측 마스크 (`1`=관측, `0`=결측)
- `method` : `"TPS"` 또는 `"REG"` (결측 보간 방식)
- `tol` : 수렴 임계값 (예: `1e-6`)
- `max_iter` : 최대 반복 횟수 (예: `50`)

## 보조 함수 아이디어
- `center_scale(Y)` : 표본을 중심화하고 스케일 정규화 (부분 정렬 시에도 활용)
- `partial_procrustes(A, B, mask)` : 공통 관측 랜드마크만으로 B→A 정렬 변환 `(R, s, t)` 추정
- `GPA(Y)` : 모든 표본이 완전할 때 수행하는 일반 GPA 루프 (센터링→평균→재정렬)
- `TPS_fit(source_pts, target_pts)` / `TPS_apply(model, pts)` : TPS 기반 결측 추정 지원
- `REG_fit_predict(X_complete, target_lm)` : 회귀(릿지 등)로 결측 랜드마크 좌표 예측

## 반복 루프 개요
초기 단계에서는 빠른 임시 채우기로 시작하고, 이후 부분 Procrustes + 보간 + GPA 반복으로 수렴을 확인한다.

```text
# 0) 초기화
X_filled = copy(X)
for n in 1..N:
  for k in 1..K:
    if M[n,k] == 0:
      X_filled[n,k] = mean_of_observed_landmarks(X, k across specimens)

prev_mu = None
for iter in 1..max_iter:
  # 1) 표본별 부분 정렬 및 결측 보간
  for specimen n:
    observed_idx = { k | M[n,k] == 1 }
    missing_idx  = { k | M[n,k] == 0 }
    if missing_idx is empty: continue

    ref = compute_current_reference(X_filled)  # 평균 형상 등
    Xn_aligned = partial_procrustes_align(X_filled[n], ref, observed_idx)

    if method == "TPS":
      X_filled[n, missing_idx] = TPS_predict(ref, Xn_aligned, observed_idx)
    else:  # REG
      for landmark k in missing_idx:
        candidates = specimens with landmark k observed
        if candidates too few:
          X_filled[n,k] = ref[k]
        else:
          model = REG_fit(X_filled[candidates, observed_idx], targets=k)
          X_filled[n,k] = REG_predict(model, X_filled[n, observed_idx])

  # 2) GPA 수행
  (Y_aligned, mu) = GPA(X_filled)

  # 3) 수렴 검사
  if prev_mu is not None and norm(mu - prev_mu) / norm(prev_mu) < tol:
    break
  prev_mu = mu

  # (선택) 세미랜드마크 슬라이딩 등 후속 처리 가능
```

## 최종 산출물
- `Y_aligned` : GPA 결과 정렬 좌표 `(N, K, D)`
- `mu` : 최종 평균 형상 `(K, D)`
- `X_imputed` : 원 좌표계 기준으로 결측이 채워진 배열 (필요 시 보존)
- `meta` : 반복 횟수, 수렴 여부, 랜드마크/표본별 보간 방식 로그 등

## 구현 시 고려 사항
- 참조 형상은 반복마다 업데이트된 평균 형상을 사용하거나 관측치가 풍부한 표본을 선택.
- 회귀 사용 시 변수 수가 많고 표본 수가 적으면 과적합 위험이 있으므로 PCA 축소나 릿지/PLS 활용 검토.
- TPS는 관측점이 부족하거나 기하가 열악한 경우 불안정하므로, 가중치 조정이나 앙상블 접근을 고려.
- 수렴 조건은 평균 형상 변화 외에 결측 좌표 변화량도 함께 모니터링하면 안정적.
- 어떤 표본/랜드마크가 어떤 방식으로 보간되었는지 기록해 재현성과 보고용 자료로 활용.
```
