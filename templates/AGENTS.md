# 프로젝트: <이름> — <한 줄 설명>

> Claude Code(`CLAUDE.md` 가 이 파일을 import)와 Codex 가 함께 읽는 프로젝트 규칙의 정본.
> 규칙 한 줄마다 실제로 겪은 실패나 명시적 결정이 근거여야 한다. 반복되는 실수는 여기보다 훅·테스트·`jig.json` 으로 옮긴다.

## 문서 (작업 전 읽을 것)

| 파일 | 언제 읽나 |
|---|---|
| `docs/PRD.md` | 기능 범위를 판단할 때 — 「하지 않는 것」 절이 경계 |
| `docs/ARCHITECTURE.md` | 구현할 때 |
| `docs/adr/` | 설계 결정을 바꾸거나 추가할 때 |
| `docs/GLOSSARY.md` | 이름을 지을 때 — 코드 식별자는 여기 것을 그대로 |
| `docs/engineering-notes.md` | 처음 만지는 영역에 들어갈 때 — 겪은 함정 |
| `docs/specs/` | 진행 중인 변경의 명세·계획 (`status: approved` 인 것만 구현 대상) |

## 기술 스택
- <언어/런타임 버전> [ADR-0001](docs/adr/0001-stack.md)
- <프레임워크·저장소·테스트 도구>

## 아키텍처 규칙
- CRITICAL: <어기면 안 되는 의존·경계 규칙>
- CRITICAL: 비밀값은 환경변수에서만 읽는다. 코드·로그·테스트 픽스처에 넣지 않는다.

## 작업 방식 (jig)
- 변경은 `/jig:spec` → 사용자 승인 → `/jig:build` 순서로 한다. 승인된 명세 없이 기능 코드를 쓰지 않는다.
- CRITICAL: 테스트를 먼저 쓰고 실패를 확인한 뒤 구현한다 (TDD). 훅이 `jig.json` 의 `tdd` 규칙으로 강제한다.
- 완료는 증거로 판단한다: 실행한 명령과 결과를 명세의 `log.md` 에 남긴다. "될 것이다"는 완료가 아니다.
- 명세·문서·코드가 서로 다르면 스스로 고르지 말고 사용자에게 묻는다.
- `jig.json` 은 검증 기준이다. 바꿔야 하면 이유를 대고 사용자 승인을 받는다.
- 커밋은 conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

## 명령어
```bash
<설치>
<개발 서버>
<테스트>      # = jig.json commands.test
<린트>        # = jig.json commands.lint
```
