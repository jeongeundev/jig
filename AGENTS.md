# 프로젝트: jig — 개인 하네스 플러그인

> 이 저장소를 고치는 에이전트를 위한 규칙. 프로젝트에 깔리는 규칙 원본은 `templates/AGENTS.md` 이고, 이 파일과 다르다.

## 구조
- `skills/*/SKILL.md` — Claude Code 와 Codex 가 같은 파일을 읽는다. 도구 전용 문법(특정 도구 이름에만 의존하는 지시)을 넣지 않는다. 필요하면 "서브에이전트(Codex 면 새 세션)"처럼 둘 다 적는다.
- `hooks/jig_hooks.py` — 훅 판정 규칙은 이 파일 한 곳에만 둔다. Claude/Codex 차이는 `--codex` 출력 형식뿐.
- `templates/` — 프로젝트에 복사되는 원본. 스택 이름은 `jig-config.md` 예시에만 둔다.

## 규칙
- CRITICAL: 훅은 `jig.json` 이 없는 프로젝트에서 아무것도 하지 않아야 한다 (bash 위험 명령 차단만 예외). 전역 설치되기 때문이다.
- CRITICAL: `hooks/jig_hooks.py` 는 표준 라이브러리만 쓴다. 설치 단계를 늘리지 않기 위해서다.
- 훅 동작을 바꾸면 `tests/test_hooks.py` 에 테스트를 먼저 추가한다.
- 스킬은 짧게 유지한다. 규칙 한 줄마다 실제 프로젝트에서 겪은 실패나 명시적 결정이 근거여야 한다.
- 버전은 `.claude-plugin/plugin.json` 과 `.codex-plugin/plugin.json` 을 같이 올린다.
- 커밋은 conventional commits.

## 명령어
```bash
python3 -m pytest -q tests      # 훅 테스트
claude plugin validate .        # 매니페스트 검증
```
