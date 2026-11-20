# jig.json

프로젝트 루트에 두는, 스택별 정보가 모이는 유일한 파일. jig 훅과 CI 가 이 파일만 읽는다.
없으면 jig 훅은 아무것도 하지 않는다(다른 프로젝트에 영향 없음).

```jsonc
{
  "commands": {
    "test":       "전체 테스트 명령",                       // Stop 훅(관련 테스트를 못 찾을 때)과 CI
    "test_files": "바뀐 파일의 테스트만 돌리는 명령 {files}", // 선택. Stop 훅이 우선 사용
    "lint":       "린트 명령",                              // 선택
    "typecheck":  "타입 검사 명령"                          // 선택
  },
  "tdd": {
    "source": ["테스트가 필요한 소스 glob"],
    "roots":  ["{path} 계산 때 앞에서 떼어낼 디렉토리"],
    "tests":  ["기대 테스트 경로 템플릿 — 하나라도 있으면 통과"],
    "exempt": ["source 중 테스트가 필요 없는 glob"]
  }
}
```

템플릿 자리표시자 (`src/app/core.py` 기준, `roots: ["src"]`):
`{dir}`=`src/app` · `{path}`=`app` · `{name}`=`core` · `{ext}`=`py`

규칙:
- 테스트 파일(`test_*`, `*_test.*`, `*.test.*`, `*.spec.*`, `tests/`·`__tests__/` 아래)은 항상 통과.
- `*.md`, `docs/**` 만 바뀐 턴은 Stop 검증을 건너뛴다.
- 명령은 프로젝트 루트에서 셸로 실행된다. 이미 `AGENTS.md` 「명령어」에 있는 것과 같아야 한다.
- 처음엔 좁게 시작한다. `source` 를 도메인·서비스 계층으로만 잡고, 화면·설정·생성 코드는 넣지 않는다.

## 예시

Python (uv, pytest, ruff, src 레이아웃, tests 가 src 구조를 따름):
```json
{
  "commands": {
    "test": "uv run pytest -q",
    "test_files": "uv run pytest -q {files}",
    "lint": "uv run ruff check ."
  },
  "tdd": {
    "source": ["src/**/*.py"],
    "roots": ["src"],
    "tests": ["tests/{path}/test_{name}.py", "tests/test_{name}.py"],
    "exempt": ["**/__init__.py", "**/__main__.py"]
  }
}
```

TypeScript (pnpm, vitest, 같은 폴더 colocated 테스트):
```json
{
  "commands": {
    "test": "pnpm vitest run",
    "test_files": "pnpm vitest run {files}",
    "lint": "pnpm eslint .",
    "typecheck": "pnpm tsc --noEmit"
  },
  "tdd": {
    "source": ["src/lib/**/*.ts", "src/server/**/*.ts"],
    "tests": ["{dir}/{name}.test.{ext}", "{dir}/__tests__/{name}.test.{ext}"],
    "exempt": ["**/*.d.ts", "**/types.ts", "**/index.ts"]
  }
}
```

Go:
```json
{
  "commands": { "test": "go test ./...", "lint": "go vet ./..." },
  "tdd": { "source": ["**/*.go"], "tests": ["{dir}/{name}_test.go"], "exempt": ["cmd/**", "**/main.go"] }
}
```
