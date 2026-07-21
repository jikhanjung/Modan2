# 0.1.11에서 데이터가 사라져 보이던 문제 (내가 만든 회귀)

## 날짜
2026-07-21

## 증상

0.1.9까지 잘 쓰던 DB로 0.1.11을 실행하니 **프로그램은 뜨는데 데이터가 전부
비어 있었다.**

## 원인

**devlog 235의 `--db` 수정이 만든 회귀다.**

`ApplicationSetup.__init__`은 이렇게 되어 있었다:

```python
self.db_path = db_path or self._get_default_db_path()   # -> ~/.modan2/modan2.db
```

그런데 `~/.modan2/modan2.db`는 **이 앱의 데이터베이스였던 적이 없다.** 실제
위치는 `MdModel`의 모듈 수준 기본값인 `<user>/PaleoBytes/Modan2/Modan2.db`다.

지금까지는 이 잘못된 기본값이 드러나지 않았다. `_prepare_database`가
`MdModel.DATABASE_PATH = self.db_path`로 **아무도 읽지 않는 속성**에 값을
넣었을 뿐이라 아무 효과가 없었기 때문이다(그래서 `--db`도 무시됐다).

devlog 235에서 그 줄을 실제로 동작하는 `MdModel.set_database_path()`로
바꾸면서, **잘못된 기본값이 비로소 효력을 갖게 됐다.** `--db` 없이 실행하면
`~/.modan2/modan2.db`라는 빈 파일을 열고 001부터 마이그레이션을 새로 돌린다.

사용자 로그가 그대로 보여준다:

```
(0.1.10) MdModel - database path: C:\Users\kopri\PaleoBytes\Modan2\Modan2.db
(0.1.11) MdModel - database path set to C:\Users\kopri\.modan2\modan2.db
(0.1.11) peewee_migrate - Migrate "001_20240305"
```

**데이터는 유실되지 않았다.** 원래 위치에 그대로 있고 앱이 다른 곳을 봤을
뿐이다.

## 수정

`ApplicationSetup`은 `--db`로 **명시된 경우에만** 경로를 바꾼다:

```python
self.db_path = db_path          # 없으면 None
...
if self.db_path:
    MdModel.set_database_path(self.db_path)
else:
    self.db_path = MdModel.database_path   # 로깅용 실제 경로
```

`_get_default_db_path()`는 삭제했다. 존재한 적 없는 경로를 지어내는 함수라
남겨두면 같은 실수가 반복된다.

## 배운 것

죽은 코드를 되살릴 때는 **그 코드가 무엇을 하려던 것인지**까지 확인해야
한다. `DATABASE_PATH` 대입은 아무 일도 하지 않았지만, 그 옆의
`_get_default_db_path()`는 틀린 값을 들고 있었다. 죽은 줄만 고치고 그것이
참조하던 값을 검증하지 않아, 무해했던 버그를 유해하게 만들었다.

## 테스트 (`tests/test_database_path.py`)

- `--db` 없이 시작하면 `set_database_path`가 **호출되지 않고** 기본 경로가
  유지되는지.
- `--db`가 있으면 그 경로로 전달되는지.
- `_get_default_db_path`가 다시 생기지 않았는지 (이름으로 못 박아 둠).

백업 동작도 함께 고정했다(사용자 확인 요청):

- 백업이 **마이그레이션 이전 상태**로 저장되는지 — 스냅샷의 존재 이유다.
  006 직전 상태의 DB로 실행해 백업본에 `chart_settings_json`이 없고 실제
  파일에는 있는 것을 확인.
- 백업 파일명이 **실제 사용 중인 파일 기준**이라 `--db`로 연 DB가 기본 DB의
  백업을 덮어쓰지 않는지.
- 새로 만드는 DB는 백업할 것이 없는지.

## 사용자 조치

다음 빌드를 설치하면 원래 데이터가 그대로 보인다. `~/.modan2/modan2.db`
(0.1.11이 만든 빈 파일)는 지워도 되고 그냥 둬도 무방하다.
