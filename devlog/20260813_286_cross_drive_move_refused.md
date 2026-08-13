# 다른 드라이브로는 이전할 수 없었다 — 그게 이전 기능의 존재 이유인데

## 날짜
2026-08-13

## 증상

`C:\Users\...\PaleoBytes\Modan2` 에서 `D:\Modan2` 로 옮기려 하면 **"같은
드라이브가 아니다"** 라는 오류가 났다.

## 원인 — 한 줄

`describe_move_problem` 의 포함 관계 검사다 (`MdUtils.py:635`):

```python
if os.path.commonpath([source, destination]) == source:
```

**`ntpath.commonpath` 는 두 경로의 드라이브가 다르면 `ValueError` 를 던진다.**

```
ValueError: Paths don't have the same drive
```

POSIX에서는 서로 다른 마운트 아래의 경로에도 조용히 `/` 를 돌려준다. **개발
머신에서는 재현이 불가능한 종류다.**

## 이게 왜 단순한 오류 메시지 이상인가

두 가지가 겹친다.

**1. 하필 실패하지 않기로 되어 있는 함수에서 터졌다.** `describe_move_problem` 의
독스트링은 이렇게 시작한다 — *"Checked before anything is touched, so the answer
can be a message rather than a half-finished move."* 문제를 **메시지로 바꾸는 것이
존재 이유인 함수가 예외를 던졌다.**

**2. 이전 제안 자체가 뜨지 않았다.** 호출부(`preferences_dialog.py:949`)는 이렇다:

```python
if mu.describe_move_problem(source, folder) is None:
    choice = self._ask_about_moving(source, folder)
```

예외가 여기서 밖으로 나가므로 `_ask_about_moving` 에 **도달하지 못한다.** 즉
Windows에서 **드라이브를 건너는 이전은 아예 불가능했다.**

그리고 드라이브를 건너는 것이 **이 기능을 쓰는 주된 이유다.** devlog 282가 이전
기능을 만든 근거가 "더 큰 드라이브로 옮기고 싶다" 였고, 같은 드라이브 안에서의
이동은 부수적인 경우다. **기능의 주 사용 사례가 주 플랫폼에서 동작하지 않았다.**

## 고친 것

`commonpath` 를 쓰지 않는 `_is_within` 으로 교체했다. 정규화한 접두사를 비교하면
드라이브가 다를 때 **예외 없이 그냥 일치하지 않는다** — 원하는 답 그대로다.

```python
directory = _path.normcase(_path.abspath(directory)).rstrip("\\/")
path = _path.normcase(_path.abspath(path))
return path == directory or path.startswith(directory + _path.sep)
```

- `normcase` 가 Windows에서 대소문자 무시를, 다른 곳에서 구분을 담당한다.
- 뒤에 구분자를 붙이는 것은 `C:\Foo` 가 `C:\FooBar` 의 부모로 보이지 않게 한다.
- `_path` 인자는 **테스트가 어느 플랫폼에서도 Windows 의미를 확인할 수 있게** 있다.

마지막 항목이 핵심이다. **이 버그가 나간 이유가 정확히 "개발 머신에서 확인할 수
없다" 였으므로, 확인할 수 없다는 조건을 없애는 것이 수정의 일부다.** 테스트는
`ntpath` 와 `posixpath` 를 직접 넘겨 양쪽 의미를 Linux에서 검증한다.

## 기존 테스트가 못 잡은 이유

`tests/test_data_directory_move.py` 에는 포함 관계 테스트가 이미 있었다:

```python
def test_destination_inside_the_source_is_refused(self, library):
    inside = library / "data" / "somewhere"
```

`tmp_path` 아래의 실제 경로를 쓴다. **실제 경로는 항상 같은 볼륨에 있고**, 그래서
문제의 입력이 만들어지지 않는다. 진짜 파일 시스템을 쓰는 테스트는 대개 더 강한
테스트인데, 여기서는 그 점이 정확히 사각지대를 만들었다 — **테스트가 만들 수 있는
경로의 집합이 사용자가 입력할 수 있는 경로의 집합보다 좁다.**

## 관련해서 남겨 두는 것

`_move_library` 는 `mu.DataDirectoryMoveError` 만 잡는다. 그 밖의 예외가 이전
도중에 나면 `_restore_after_failed_move` 가 실행되지 않아 **데이터베이스가 닫힌 채
남는다.** 이번 버그는 이전이 시작되기 전에 터졌으므로 그 경로를 타지 않았지만,
좁은 `except` 절이라는 점은 같다. 별건으로 다룬다.
