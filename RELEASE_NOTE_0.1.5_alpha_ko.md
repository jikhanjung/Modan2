# Modan2 v0.1.5 Alpha Release Note

**⚠️ 알파 버전 안내: 이 버전은 테스트 목적으로 제공되며 실제 연구에 사용하기 전 충분한 검증을 권장합니다.**

## 주요 신기능

### 📦 JSON+ZIP 데이터셋 패키징 시스템
완전한 데이터셋 백업 및 공유를 위한 혁신적인 export/import 시스템을 도입했습니다.

**핵심 기능:**
- **완전한 데이터 보존**: 랜드마크, 변수, 와이어프레임, 폴리곤, 베이스라인, 이미지, 3D 모델을 모두 포함
- **구조화된 패키징**: ZIP 내에 체계적인 폴더 구조 (dataset.json, images/, models/)
- **손실 없는 라운드트립**: Export → Import 과정에서 모든 데이터가 정확히 보존
- **안전한 Import**: Zip Slip 공격 방지 및 트랜잭션 기반 롤백 기능
- **진행률 표시**: 대용량 데이터셋 처리 시 실시간 진행률 및 크기 추정

**파일 구조 예시:**
```
my_dataset.zip
├── dataset.json          # 모든 메타데이터 + 랜드마크 + 변수
├── images/              # 이미지 파일들
│   ├── 123.jpg
│   └── 456.png
└── models/              # 3D 모델 파일들
    ├── 123.obj
    └── 456.ply
```

**기존 형식과의 차이점:**
- **TPS/NTS**: 랜드마크만 → **JSON+ZIP**: 모든 데이터 + 파일
- **Morphologika**: 랜드마크 + 변수 + 이미지 → **JSON+ZIP**: + 3D 모델 + 기하학적 구조
- **CSV/Excel**: 기본 데이터만 → **JSON+ZIP**: 완전한 데이터셋 아카이브

### 🛡️ 보안 및 안정성 강화
- **Zip Slip 방어**: 악의적인 ZIP 파일로부터 시스템 보호
- **원자적 트랜잭션**: Import 실패 시 데이터베이스 자동 롤백
- **파일 무결성 검증**: MD5 체크섬을 통한 파일 검증
- **충돌 해결**: 동일 이름 데이터셋 자동 번호 추가 (예: "Dataset (1)")

### 🎯 향상된 사용자 경험
- **Export Dialog 확장**: 기존 대화상자에 "JSON+ZIP Package" 옵션 추가
- **파일 포함 토글**: 이미지/3D 모델 포함 여부 선택 가능
- **크기 추정**: Export 전 예상 파일 크기 표시
- **Import Preview**: ZIP 파일 내용 미리보기 (개체 수, 차원 등)

## 기술적 개선사항

### 📋 새로운 API 함수들 (MdUtils.py)
- `serialize_dataset_to_json()`: 데이터셋을 JSON 구조로 직렬화
- `create_zip_package()`: 파일 수집 및 ZIP 패키징
- `import_dataset_from_zip()`: 안전한 ZIP 기반 데이터셋 Import
- `collect_dataset_files()`: 데이터셋 관련 파일 경로 수집
- `safe_extract_zip()`: 보안 검증을 통한 ZIP 압축 해제
- `validate_json_schema()`: JSON 스키마 검증 및 에러 보고

### 🏗️ JSON Schema v1.1
완전한 데이터셋 메타데이터를 포함하는 확장된 스키마:
```json
{
  "format_version": "1.1",
  "dataset": {
    "wireframe": [[1,2], [2,3], ...],    // 와이어프레임 정보
    "polygons": [[1,2,3], ...],          // 폴리곤 정보
    "baseline": [1,2],                   // 베이스라인 (2점 또는 3점)
    "variables": ["Sex", "Age", ...]     // 변수 목록
  },
  "objects": [
    {
      "landmarks": [[x,y], [null,y], ...], // null 좌표 지원
      "pixels_per_mm": 3.2,                // 스케일 정보
      "sequence": 1,                       // 객체 순서
      "files": {                           // 첨부 파일 메타데이터
        "image": {...},
        "model": {...}
      }
    }
  ]
}
```

### 💾 크로스 플랫폼 호환성
- UTF-8 인코딩으로 한국어 파일명 지원
- Windows, macOS, Linux 경로 처리 통합
- 파일 시스템 안전성 검증

## 📚 문서화
- **구현 계획서**: `devlog/20250911_047_json_zip_dataset_export_implementation_plan.md`
- **수정 계획서**: `devlog/20250911_048_json_zip_dataset_export_implementation_plan_revised.md`
- 상세한 API 문서 및 사용 예제

## 다운로드

**⚠️ 주의: 알파 버전은 테스트 목적으로만 사용하세요.**

[릴리즈 페이지](https://github.com/jikhanjung/Modan2/releases)에서 플랫폼에 맞는 버전을 다운로드하세요:

- **Windows**: `Modan2-Windows-Installer-v0.1.5-alpha-build*.zip`
- **macOS**: `Modan2-macOS-Installer-v0.1.5-alpha-build*.dmg`
- **Linux**: `Modan2-Linux-v0.1.5-alpha-build*.AppImage`

## 시스템 요구사항
- Python 3.11 이상
- NumPy 2.0+
- PyQt5
- 여유 디스크 공간 (대용량 데이터셋 Export/Import 시)

## 사용법

### 데이터셋 Export
1. 메뉴: **Dataset > Export Dataset**
2. **"JSON+ZIP Package (Complete Dataset)"** 선택
3. **"Include image and model files"** 체크 (필요한 경우)
4. 저장 위치 선택 후 Export

### 데이터셋 Import
1. 메뉴: **Dataset > Import Dataset**
2. **"JSON+ZIP"** 형식 선택
3. ZIP 파일 선택 후 Import

## 알려진 제한사항
- 매우 큰 데이터셋(1GB+)의 경우 메모리 사용량 증가 가능
- Import 중 네트워크 드라이브에서 성능 저하 가능
- 일부 안티바이러스 소프트웨어에서 ZIP 파일 검사로 인한 지연

## 피드백 및 문제 신고
이 알파 버전을 사용하면서 발견한 문제나 개선 사항은 다음 방법으로 신고해 주세요:
- **GitHub Issues**: [https://github.com/jikhanjung/Modan2/issues](https://github.com/jikhanjung/Modan2/issues)
- **이메일**: honestjung@gmail.com

## 다음 계획 (v0.1.5 정식 버전)
- 사용자 피드백 반영 및 버그 수정
- 성능 최적화 (대용량 파일 처리)
- 추가 검증 테스트 및 문서화
- 배치 Export 기능 (여러 데이터셋 동시 처리)

---

**참고**: 이 버전의 새로운 JSON+ZIP 형식은 기존 TPS, Morphologika, NTS 형식과 완전히 호환됩니다. 기존 형식들은 계속 지원되며, JSON+ZIP은 완전한 백업 및 공유를 위한 추가 옵션입니다.
