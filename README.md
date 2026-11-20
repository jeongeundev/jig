# jig

프로젝트마다 하네스를 처음부터 다시 만들지 않기 위한 개인 플러그인. 지그(jig)가 가공물을 고정해 매번 같은 부품이 나오게 하듯, 어떤 프로젝트든 같은 흐름으로 일하게 한다.

```
새 프로젝트  /jig:bootstrap ─┐
기존 프로젝트 /jig:adopt ─────┴→ /jig:spec → (승인) → /jig:build → /jig:verify → PR
```

| 스킬 | 하는 일 |
|---|---|
| `bootstrap` | 의도·범위·스택을 묻고, 공식 생성기로 뼈대를 만든 뒤 하네스(AGENTS.md, docs, jig.json, CI)를 채운다 |
| `adopt` | 기존 코드·문서·이력을 읽고 실제에 맞는 하네스를 만든다. 문서와 코드가 다르면 묻는다 |
| `spec` | 결정 목록 → 사용자 몫은 질문 → 독립 서브에이전트 검사 → `docs/specs/NNNN-slug/{spec,plan}.md` |
| `build` | 승인된 명세를 Red → Green → Refactor 로 구현하고 작업마다 실행 증거를 `log.md` 에 남긴다. 명세 기준 리뷰 후 PR |
| `verify` | 프로젝트 전용 실행 검증 절차를 만들고(없을 때) 실제로 돌려 증거를 남긴다 |

## 훅 (스택 무관)

훅은 프로젝트 루트의 `jig.json` 만 읽는다. **`jig.json` 이 없는 프로젝트에서는 TDD·검증 훅이 아무것도 하지 않는다.**

| 훅 | 시점 | 동작 |
|---|---|---|
| tdd | 파일 편집 전 | `tdd.source` 에 해당하는 파일인데 `tdd.tests` 경로에 테스트가 없으면 차단. `jig.json` 수정은 사용자 승인 요청 |
| bash | 셸 실행 전 | `rm -rf`, `git push --force`, `git reset --hard`, `git clean -f`, `DROP TABLE` 차단 (모든 프로젝트) |
| verify | 턴 종료 | 바뀐 소스의 테스트 존재 확인 + `commands` 실행. 실패하면 에이전트에게 돌려보내 고치게 함 |

`jig.json` 형식과 Python/TypeScript/Go 예시: [templates/jig-config.md](templates/jig-config.md)

## 설치

필요한 것: `python3` (훅이 표준 라이브러리만 사용), `git`.

**Claude Code**
```text
/plugin marketplace add jeongeundev/jig
/plugin install jig@jig
```
개발 중에는 로컬 경로로: `/plugin marketplace add /path/to/jig`

**Codex**
```bash
codex plugin marketplace add jeongeundev/jig
codex plugin add jig@jig
git clone https://github.com/jeongeundev/jig ~/.jig && python3 ~/.jig/codex/install-hooks.py   # 훅은 전역 hooks.json 에 등록
```
`install-hooks.py --dry-run` 으로 미리 보고, `--uninstall` 로 제거한다.

## 구조

```
.claude-plugin/   Claude Code 플러그인·마켓플레이스 매니페스트
.codex-plugin/    Codex 플러그인 매니페스트      (.agents/plugins/ 는 Codex 마켓플레이스)
skills/           다섯 스킬 — 두 도구가 같은 SKILL.md 를 읽는다
hooks/            jig_hooks.py (훅 본체), hooks.json (Claude 등록)
codex/            Codex 전역 훅 등록 스크립트
templates/        프로젝트에 깔리는 하네스 원본
tests/            훅 테스트
```

## 바탕이 된 것

- 내 이전 프로젝트: OpenArchive(문서 표·실패 기록), runloom(AGENTS.md 정본, 결정 목록과 독립 검사, TDD 가드·검증 훅)
- [dryforge](https://github.com/prekuter/dryforge) — 의도 확정 후 실행, 증거 기반 완료, 기존 프로젝트 migration
- [obra/superpowers](https://github.com/obra/superpowers) — 계획 → 작업별 구현 → 명세·품질 2단 리뷰
- [pstack](https://github.com/backnotprop/pstack) — 프로젝트 전용 검증 스킬
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) — 기존 코드 변경은 현재 동작과의 차이로 명세

## 개발

```bash
python3 -m pytest -q tests        # 훅 테스트
claude plugin validate .          # 매니페스트 검증
```
규칙은 [AGENTS.md](AGENTS.md).
