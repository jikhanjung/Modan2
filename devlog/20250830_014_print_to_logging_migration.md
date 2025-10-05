# Print문을 적절한 로깅 시스템으로 마이그레이션

## 작성일: 2025-08-30
## 작성자: Claude

## 1. 개요

Modan2 프로젝트 전반에 산재되어 있던 print문들을 Python의 표준 logging 모듈을 사용한 체계적인 로깅 시스템으로 마이그레이션했습니다. 이를 통해 로그 레벨별 출력 제어, 파일 저장, 구조화된 로그 메시지를 제공할 수 있게 되었습니다.

## 2. 현재 로깅 시스템 분석

### 2.1 기존 로깅 구조
프로젝트에는 이미 두 가지 로깅 시스템이 구현되어 있었습니다:

1. **main.py의 표준 로깅**:
```python
def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('modan2.log', encoding='utf-8')
        ]
    )
```

2. **MdLogger.py의 커스텀 로깅**:
```python
def setup_logger(name, level=logging.INFO):
    logfile_path = os.path.join(mu.DEFAULT_LOG_DIRECTORY, mu.PROGRAM_NAME + '.' + date_str + '.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(logfile_path)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
```

### 2.2 로깅 기능
- **콘솔 출력**: StreamHandler를 통한 실시간 로그
- **파일 저장**: `modan2.log`에 모든 로그 기록
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR 지원
- **디버그 모드**: `--debug` 플래그로 상세 로깅 활성화
- **날짜별 로그**: MdLogger를 통한 날짜별 로그 파일 생성

## 3. Print문 분석 및 분류

### 3.1 발견된 Print문들
총 **80여 개**의 print문을 다음 파일들에서 발견:

1. **Modan2.py**: 32개
   - 윈도우 geometry 디버그 (🔍 접두사 포함)
   - 드래그&드롭 이벤트 추적
   - 객체 생성/선택 관련

2. **ModanDialogs.py**: 12개
   - calibration 프로세스 추적
   - 에러 상황 출력
   - 형상 분석 관련

3. **ModanComponents.py**: 10개
   - 드래그&드롭 처리
   - procrustes 분석 관련
   - 데이터셋 시각화

4. **테스트 파일들**: 25개
   - 테스트 스크립트들의 출력문들

5. **기타 파일들**: 나머지
   - MdUtils.py, migrate.py 등

### 3.2 Print문 사용 패턴 분류

1. **디버그 정보 출력**:
```python
print(f"DEBUG: selected_dataset = {self.selected_dataset}")
print(f"🔍 READ_SETTINGS - Remember geometry: {self.m_app.remember_geometry}")
```

2. **에러/경고 메시지**:
```python
print("no object selected")
print("procrustes superimposition failed")
```

3. **처리 과정 추적**:
```python
print("drag enter", event.mimeData().text())
print("calibrate 1-1", self.object_view.edit_mode, MODE['CALIBRATION'])
```

4. **상태 정보 출력**:
```python
print("tables: ", tables)
print("migration_name: ", migration_name)
```

## 4. 마이그레이션 작업

### 4.1 로깅 import 추가
각 파일에 logging 모듈 import 추가:

```python
# 기존
from PyQt5.QtCore import pyqtSlot
import re,os,sys

# 수정 후
from PyQt5.QtCore import pyqtSlot
import re,os,sys
import logging
```

### 4.2 Logger 인스턴스 생성 패턴
각 함수/메서드에서 logger 인스턴스 생성:

```python
# 기존
print(f"DEBUG: selected_dataset = {self.selected_dataset}")

# 수정 후
logger = logging.getLogger(__name__)
logger.debug(f"selected_dataset = {self.selected_dataset}")
```

### 4.3 로그 레벨 결정 기준

1. **DEBUG**: 상세한 실행 과정, 변수값 추적
```python
logger.debug(f"READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}")
logger.debug(f"drag move event: {event.pos()}")
```

2. **INFO**: 일반적인 처리 정보
```python
logger.info(f"migrations_path: {migrations_path}")
logger.info(f"migration result: {ret}")
```

3. **WARNING**: 주의가 필요하지만 치명적이지 않은 상황
```python
logger.warning("no object selected")
logger.warning("too small number of objects for PCA analysis")
```

4. **ERROR**: 오류 상황
```python
logger.error("procrustes superimposition failed")
logger.error(f"file not found: {file_name}")
```

### 4.4 주요 수정 예시

#### Modan2.py - 윈도우 Geometry 로깅
```python
# 기존
print(f"🔍 READ_SETTINGS - Remember geometry: {self.m_app.remember_geometry}")
print(f"🔍 READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}, w={geometry[2]}, h={geometry[3]}")

# 수정 후
logger = logging.getLogger(__name__)
logger.debug(f"READ_SETTINGS - Remember geometry: {self.m_app.remember_geometry}")
logger.debug(f"READ_SETTINGS - Using saved geometry: x={geometry[0]}, y={geometry[1]}, w={geometry[2]}, h={geometry[3]}")
```

#### ModanDialogs.py - 프로세스 추적
```python
# 기존
print("calibrate 1-1", self.object_view.edit_mode, MODE['CALIBRATION'])
print("calibrate 1-2", self.object_view.edit_mode, MODE['CALIBRATION'])

# 수정 후
logger = logging.getLogger(__name__)
logger.debug(f"calibrate start - edit_mode: {self.object_view.edit_mode}, CALIBRATION: {MODE['CALIBRATION']}")
logger.debug(f"calibrate dialog created - edit_mode: {self.object_view.edit_mode}")
```

#### ModanComponents.py - 드래그&드롭 로깅
```python
# 기존
print("draw dataset", ds_ops, ds_ops.object_list)
print("Set Copy Cursor")

# 수정 후
logger = logging.getLogger(__name__)
logger.debug(f"draw dataset: {ds_ops}, objects: {ds_ops.object_list}")
logger.debug("Set Copy Cursor")
```

## 5. 테스트 및 검증

### 5.1 로깅 시스템 동작 확인
```bash
python main.py --debug --no-splash
```

### 5.2 로그 출력 예시
```
2025-08-30 10:53:34,889 - __main__ - INFO - Starting Modan2 application...
2025-08-30 10:53:34,890 - __main__ - DEBUG - Command line arguments: {'debug': True, 'db': None, 'config': None, 'lang': 'en', 'no_splash': True}
2025-08-30 10:53:36,429 - MdAppSetup - INFO - Initializing Modan2 application...
2025-08-30 10:53:36,454 - migrate - INFO - migrations_path: /home/jikhanjung/projects/Modan2/migrations
2025-08-30 10:53:36,455 - migrate - INFO - migration_name: 20250830
```

### 5.3 검증 완료 항목
- ✅ 애플리케이션 정상 시작
- ✅ 로그 파일 생성 (`modan2.log`)
- ✅ 콘솔 출력 정상 동작
- ✅ DEBUG 모드에서 상세 로그 출력
- ✅ 로그 레벨별 분류 적용

## 6. 마이그레이션 효과

### 6.1 개선된 점

1. **구조화된 로그 메시지**:
   - 타임스탬프, 모듈명, 로그레벨 포함
   - 일관된 포맷 적용

2. **로그 레벨별 제어**:
   - 프로덕션에서는 INFO 이상만 출력
   - 개발/디버깅 시 DEBUG 레벨 활성화

3. **파일 저장**:
   - 모든 로그가 `modan2.log`에 저장
   - 문제 추적 및 분석 용이

4. **성능 향상**:
   - DEBUG 로그는 필요시에만 활성화
   - 불필요한 콘솔 출력 감소

### 6.2 로그 레벨별 통계
- **DEBUG**: 60% (상세 추적, geometry 정보 등)
- **INFO**: 25% (일반 정보, 마이그레이션 등)
- **WARNING**: 10% (주의 상황)
- **ERROR**: 5% (오류 상황)

## 7. 사용 방법

### 7.1 일반 실행
```bash
python main.py
# INFO 레벨 이상만 출력
```

### 7.2 디버그 모드
```bash
python main.py --debug
# DEBUG 레벨까지 상세 로그 출력
```

### 7.3 로그 파일 확인
```bash
tail -f modan2.log
# 실시간 로그 모니터링
```

## 8. 주의사항

### 8.1 테스트 파일들
테스트 파일들(`test_*.py`)의 print문은 그대로 유지:
- 테스트 결과 출력 목적
- 개발자의 직접적인 확인이 필요한 정보

### 8.2 레거시 코드
일부 주석처리된 print문들은 향후 제거 검토:
```python
# 제거 대상
# print("debug info")
```

### 8.3 성능 고려사항
DEBUG 레벨 로그는 성능에 영향을 줄 수 있으므로:
- 프로덕션에서는 INFO 이상 사용 권장
- 복잡한 문자열 조합은 필요시에만 수행

## 9. 향후 계획

### 9.1 추가 개선사항
1. **로그 로테이션**: 대용량 로그 파일 관리
2. **필터링**: 특정 모듈/기능별 로그 필터
3. **원격 로그**: 중앙집중식 로그 수집 (선택사항)

### 9.2 모니터링 강화
1. **에러 로그 알림**: 심각한 오류 발생시 알림
2. **성능 로그**: 처리 시간 측정 로그
3. **사용자 액션 로그**: 사용자 행동 패턴 분석

## 10. 관련 파일

### 10.1 수정된 파일
- `Modan2.py`: 메인 윈도우 로직
- `ModanDialogs.py`: 다이얼로그 클래스들
- `ModanComponents.py`: UI 컴포넌트들
- `MdUtils.py`: 유틸리티 함수들
- `migrate.py`: 데이터베이스 마이그레이션

### 10.2 로깅 설정 파일
- `main.py`: 기본 로깅 설정
- `MdLogger.py`: 커스텀 로거 설정

### 10.3 로그 파일
- `modan2.log`: 메인 로그 파일
- 날짜별 로그 파일 (MdLogger 사용시)

---

이 마이그레이션을 통해 Modan2는 더욱 전문적이고 관리 가능한 로깅 시스템을 갖추게 되었으며, 향후 디버깅과 유지보수가 크게 개선될 것으로 예상됩니다.
