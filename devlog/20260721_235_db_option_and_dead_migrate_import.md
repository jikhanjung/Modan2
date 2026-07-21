# `--db` 옵션 수정 및 죽은 migrate import 제거

## 날짜
2026-07-21

## 배경

0.1.10 시작 실패를 검증하려고 테스트용 DB로 앱을 띄우려다, `--db` 옵션이
동작하지 않는다는 것을 발견했다. CLAUDE.md에도 지원 옵션으로 적혀 있다.

## 원인

`MdAppSetup._prepare_database`가 이렇게 하고 있었다:

```python
MdModel.DATABASE_PATH = self.db_path
```

그런데 **`MdModel`에는 `DATABASE_PATH`라는 이름이 없다.** 존재하지 않는 속성을
만들어 놓을 뿐이고 읽는 곳도 없다. 실제 연결은 import 시점에 고정된다:

```python
database_path = os.path.join(mu.DEFAULT_DB_DIRECTORY, DATABASE_FILENAME)
gDatabase = SqliteDatabase(database_path, ...)
```

모든 모델이 이 `gDatabase` 객체에 바인딩되므로, 경로 문자열만 바꿔서는 아무
일도 일어나지 않는다. **`--db`를 줘도 항상 기본 DB를 썼다.**

## 수정

### `MdModel.set_database_path(path)`

peewee의 `Database.init()`으로 같은 Database 객체를 다른 파일에 다시 물린다.
모델들이 그 객체를 공유하므로 한 번에 전부 옮겨간다. 부수적으로 경로를 절대
경로로 정규화하고(`~` 확장 포함), 상위 디렉터리를 만들고, 열려 있던 연결을
닫는다.

`prepare_database`의 백업 파일명도 상수 `DATABASE_FILENAME` 대신 **실제 사용
중인 파일 이름** 기준으로 바꿨다. 그러지 않으면 `--db`로 연 DB가 기본 DB의
백업을 덮어쓴다.

### 죽은 `migrate` import 제거

`_prepare_database`에는 이런 블록이 있었다:

```python
try:
    from migrate import run_migrations
    run_migrations()
except ImportError:
    self.logger.warning("Migration module not found, skipping migrations")
```

`migrate.py`에 `run_migrations` 함수는 없다. 그래서 항상 ImportError로 끝나고
경고만 남겼다. 문제는 **import 자체가 `migrate.py` 본문을 실행**한다는 점이다 —
그 본문은 기본 DB에 별도로 접속하고 `router.create(auto=[...])`까지 돌린다.
실제 마이그레이션은 바로 앞의 `prepare_database()`가 이미 끝냈으므로 순수한
부작용이고, `--db`로 다른 DB를 지정해도 이 코드만은 기본 DB를 건드렸다.

블록을 삭제했다. 로그에서 기본 DB 접근이 사라진 것으로 확인.

## 검증

실제 Windows DB(682MB, 데이터셋 9 · 개체 901 · 분석 26 · 이미지 70)를 WSL로
복사해 사용했다. 원본은 읽기만 했다.

1. **`--db` 동작**: 지정한 파일을 쓰고(`database path set to ...`), 기본 DB는
   그대로(0 rows) 유지.
2. **0.1.10 마이그레이션 재확인**: 복사본에서 `chart_settings_json` 컬럼과 006
   기록을 제거해 **0.1.9 이전 상태로 되돌린 뒤** 앱 기동 →
   `Migrate "006_20260721"` → `Done`, 컬럼 생성, 기록 추가, **데이터 건수 불변**,
   오류 0건.

`tests/test_database_path.py` (신규 5개): 모델이 새 경로를 따라가는지, 쓰기가
그 파일에 들어가는지, 없는 디렉터리를 만드는지, 상대 경로를 절대 경로로
바꾸는지, 이전 파일의 연결을 남기지 않는지.

## 참고

이제 테스트용 DB로 앱을 띄울 수 있다:

```
python main.py --db /path/to/test.db
```
