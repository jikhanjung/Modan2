# Modan2 코드 인덱싱 구현 계획

**작성 날짜**: 2025-09-10
**작성자**: Claude (with Human Developer)
**참조 문서**: `20250909_040_code_indexing_strategy.md`

## 개요

Modan2 프로젝트의 특성(PyQt5 GUI, OpenGL 3D 렌더링, Peewee ORM)을 반영한 맞춤형 코드 인덱싱 시스템 구현 계획입니다. 기존 전략 문서를 기반으로 프로젝트별 특화 기능을 추가했습니다.

## 1. Modan2 특화 인덱스 구조

### 1.1 레벨 A: 기본 심볼 인덱스 (확장)
```json
{
  "standard": ["functions", "classes", "methods", "variables"],
  "pyqt5": ["signals", "slots", "ui_components", "actions"],
  "opengl": ["render_methods", "shader_ops", "buffer_ops"],
  "database": ["models", "queries", "migrations"]
}
```

### 1.2 레벨 B: 관계 그래프 인덱스 (확장)
- **Qt 시그널-슬롯 그래프**: 이벤트 흐름 추적
- **UI 컴포넌트 계층**: 위젯-레이아웃 관계
- **데이터 플로우**: Model → Controller → View
- **OpenGL 렌더 파이프라인**: 초기화 → 설정 → 렌더 → 정리

### 1.3 레벨 C: 의미 인덱스 (특화)
- **기능별 클러스터**: 분석, 시각화, 데이터 관리, UI
- **성능 메트릭**: Wait cursor 필요 여부, 예상 실행 시간
- **사용자 경험 태그**: 블로킹/논블로킹, 진행률 표시 여부

## 2. 심볼 카드 스키마 (Modan2 버전)

### 2.1 PyQt5 위젯 메서드 카드
```json
{
  "symbol": "DataExplorationDialog.cbxShapeGrid_state_changed",
  "kind": "qt_slot",
  "file": "ModanDialogs.py",
  "line": 2402,
  "signature": "cbxShapeGrid_state_changed(self) -> None",
  "qt_metadata": {
    "signal_source": "QCheckBox.stateChanged",
    "connected_widgets": ["sgpWidget", "plot_widget2"],
    "ui_updates": ["shape_grid", "chart_display"],
    "requires_wait_cursor": true
  },
  "calls": [
    "self.sgpWidget.show",
    "self.update_chart",
    "QApplication.setOverrideCursor"
  ],
  "database_ops": [],
  "performance": {
    "blocking": true,
    "estimated_ms": "200-500",
    "has_progress": false
  }
}
```

### 2.2 데이터베이스 모델 카드
```json
{
  "symbol": "MdAnalysis",
  "kind": "peewee_model",
  "file": "MdModel.py",
  "table": "mdanalysis",
  "fields": [
    {"name": "id", "type": "AutoField", "primary": true},
    {"name": "analysis_name", "type": "CharField", "max_length": 255},
    {"name": "dataset", "type": "ForeignKeyField", "references": "MdDataset"},
    {"name": "result", "type": "TextField", "nullable": true}
  ],
  "relationships": {
    "belongs_to": ["MdDataset"],
    "has_many": []
  },
  "used_in": [
    "ModanController.run_analysis",
    "DataExplorationDialog.__init__",
    "AnalysisResultDialog.show_result"
  ],
  "crud_operations": {
    "create": ["ModanController.run_analysis"],
    "read": ["DataExplorationDialog.load_analysis"],
    "update": ["ModanController.update_analysis"],
    "delete": ["MainWindow.delete_analysis"]
  }
}
```

### 2.3 OpenGL 렌더링 메서드 카드
```json
{
  "symbol": "ObjectViewer3D.paintGL",
  "kind": "opengl_render",
  "file": "ModanComponents.py",
  "pipeline_stage": "render",
  "gl_calls": [
    "glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)",
    "glLoadIdentity",
    "glTranslatef",
    "glRotatef",
    "glCallList"
  ],
  "prerequisites": ["initializeGL", "resizeGL"],
  "state_dependencies": [
    "self.rotation_matrix",
    "self.pan_x",
    "self.pan_y",
    "self.dolly"
  ],
  "performance": {
    "fps_impact": "high",
    "optimization_hints": ["Use VBO for large datasets", "Implement frustum culling"]
  }
}
```

## 3. UI 컴포넌트 맵 인덱스

### 3.1 다이얼로그 구조 인덱스
```json
{
  "dialog": "NewAnalysisDialog",
  "file": "ModanDialogs.py",
  "layout_hierarchy": {
    "main": "QGridLayout",
    "children": [
      {"row": 0, "widget": "edtAnalysisName", "type": "QLineEdit"},
      {"row": 1, "widget": "comboSuperimposition", "type": "QComboBox"},
      {"row": 2, "widget": "comboCvaGroupBy", "type": "QComboBox"},
      {"row": 3, "widget": "progressBar", "type": "QProgressBar"},
      {"row": 4, "widget": "lblStatus", "type": "QLabel"},
      {"row": 5, "layout": "buttonLayout", "widgets": ["btnOK", "btnCancel"]}
    ]
  },
  "signal_connections": [
    {"from": "btnOK.clicked", "to": "btnOK_clicked"},
    {"from": "btnCancel.clicked", "to": "btnCancel_clicked"},
    {"from": "controller.analysis_progress", "to": "on_analysis_progress"}
  ],
  "state_flow": {
    "initial": "input_enabled",
    "states": {
      "input_enabled": {"trigger": "btnOK_clicked", "next": "analyzing"},
      "analyzing": {
        "triggers": ["analysis_completed", "analysis_failed"],
        "next": ["completed", "error"]
      }
    }
  }
}
```

## 4. 구현 로드맵

### Phase 1: 기본 인덱싱 (1주)
- [ ] universal-ctags 설정 및 기본 심볼 추출
- [ ] ripgrep 기반 참조 검색 스크립트
- [ ] 기본 심볼 카드 생성 (Python 함수/클래스)

### Phase 2: PyQt5 특화 (1주)
- [ ] Qt 시그널-슬롯 파서 구현
- [ ] UI 파일(.ui) 파싱 및 위젯 계층 추출
- [ ] 이벤트 핸들러 맵핑

### Phase 3: 데이터베이스 & ORM (3일)
- [ ] Peewee 모델 스캔 및 스키마 추출
- [ ] CRUD 작업 위치 매핑
- [ ] 마이그레이션 히스토리 인덱싱

### Phase 4: OpenGL 파이프라인 (3일)
- [ ] GL 함수 호출 추적
- [ ] 렌더링 파이프라인 그래프 생성
- [ ] 성능 핫스팟 표시

### Phase 5: 벡터 DB & 검색 (1주)
- [ ] ChromaDB 또는 FAISS 설정
- [ ] 심볼 카드 임베딩 생성
- [ ] 자연어 검색 인터페이스

### Phase 6: CI/CD 통합 (3일)
- [ ] GitHub Actions 워크플로우
- [ ] PR 단위 증분 인덱싱
- [ ] 변경 영향 분석 리포트

## 5. 도구 스택

### 필수 도구
```yaml
indexing:
  - universal-ctags: 기본 심볼 추출
  - ripgrep: 고속 텍스트 검색
  - tree-sitter-python: AST 파싱

analysis:
  - ast (Python 내장): AST 분석
  - pycg: 호출 그래프 생성
  - pyqt5-tools: Qt 메타데이터 추출

storage:
  - SQLite: 메타데이터 저장
  - ChromaDB: 벡터 임베딩 저장
  - JSON: 심볼 카드 저장

quality:
  - ruff: 린팅 메타데이터
  - mypy: 타입 체크 (선택)
  - coverage.py: 테스트 커버리지
```

## 6. 프로젝트 구조

```
modan2_index/
├── .index/
│   ├── symbols/
│   │   ├── ctags.json
│   │   └── references.json
│   ├── graphs/
│   │   ├── call_graph.json
│   │   ├── qt_signals.json
│   │   └── gl_pipeline.json
│   ├── cards/
│   │   ├── functions/
│   │   ├── classes/
│   │   ├── models/
│   │   └── dialogs/
│   ├── vectors/
│   │   ├── index.faiss
│   │   └── metadata.db
│   └── cache/
│       └── summaries/
├── tools/
│   ├── index_builder.py
│   ├── qt_parser.py
│   ├── db_scanner.py
│   └── search_cli.py
└── config/
    ├── indexing.yaml
    └── ignore_patterns.txt
```

## 7. 사용 예시

### 7.1 CLI 검색
```bash
# 심볼 검색
$ python tools/search_cli.py --symbol "DataExploration"

# Wait cursor가 필요한 메서드 찾기
$ python tools/search_cli.py --filter "requires_wait_cursor:true"

# 특정 모델을 사용하는 모든 위치
$ python tools/search_cli.py --model "MdAnalysis" --usage

# 시그널-슬롯 체인 추적
$ python tools/search_cli.py --signal "analysis_completed" --trace
```

### 7.2 VSCode 확장
```json
{
  "modan2.showSymbolCard": true,
  "modan2.showPerformanceHints": true,
  "modan2.showQtConnections": true
}
```

## 8. 성능 메트릭 통합

### 8.1 Wait Cursor 자동 감지
```python
def analyze_method_performance(method_ast):
    """메서드가 wait cursor가 필요한지 자동 판단"""
    indicators = {
        'database_query': 100,
        'file_io': 200,
        'network_request': 500,
        'heavy_computation': 300,
        'ui_update_batch': 150
    }

    estimated_ms = sum_indicators(method_ast, indicators)
    return {
        'requires_wait_cursor': estimated_ms > 100,
        'requires_progress': estimated_ms > 1000,
        'estimated_duration': estimated_ms
    }
```

## 9. 예상 효과

### 개발 효율성
- **코드 탐색 시간 80% 감소**: 심볼 카드로 즉시 이해
- **리팩토링 안정성 향상**: 영향 범위 사전 파악
- **신규 개발자 온보딩 단축**: 3주 → 1주

### 코드 품질
- **데드 코드 자동 감지**: 참조되지 않는 심볼 식별
- **성능 이슈 사전 예방**: Wait cursor 필요 위치 자동 표시
- **테스트 커버리지 시각화**: 심볼-테스트 매핑

### 협업
- **PR 리뷰 효율화**: 변경 영향 자동 분석
- **문서화 자동화**: 심볼 카드 기반 API 문서
- **지식 공유**: 코드 의도와 관계 명시화

## 10. 다음 단계

1. **파일럿 테스트**: `MdStatistics.py` 모듈로 PoC 구현
2. **팀 리뷰**: 인덱스 스키마 및 도구 선택 확정
3. **점진적 확장**: 핵심 모듈부터 순차 적용
4. **CI 통합**: GitHub Actions 워크플로우 구성
5. **도구 개발**: VSCode 확장 또는 웹 UI 개발

## 결론

Modan2의 복잡한 아키텍처(PyQt5 + OpenGL + ORM)를 효과적으로 관리하기 위한 맞춤형 코드 인덱싱 시스템입니다. 이를 통해 대규모 리팩토링, 성능 최적화, 신기능 개발이 훨씬 안전하고 효율적으로 진행될 수 있을 것입니다.

특히 오늘 작업한 wait cursor와 progress dialog 같은 UX 개선 사항도 자동으로 추적하고 필요한 위치를 제안할 수 있어, 일관된 사용자 경험을 제공하는 데 도움이 될 것입니다.
