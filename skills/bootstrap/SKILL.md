---
name: bootstrap
description: 새 프로젝트를 jig 하네스로 시작한다 — 의도를 묻고 PRD·스택 ADR·AGENTS.md·jig.json·CI 를 만든다. 빈 폴더나 막 만든 저장소에서 "새 프로젝트 시작", "bootstrap", "/jig:bootstrap" 일 때 쓴다. 이미 코드가 있는 저장소면 adopt 를 쓴다.
---

# bootstrap — 새 프로젝트

목표: 첫 기능 명세(`/jig:spec`)를 바로 시작할 수 있는 상태. 코드는 공식 생성기가 만든 뼈대까지만 쓴다.

템플릿은 이 스킬 디렉토리 기준 `../../templates/` 에 있다. 복사한 뒤 반드시 이 프로젝트 내용으로 채운다 — 자리표시자(`<...>`)가 남은 파일은 결함이다.

## 1. 확인
- 폴더에 소스 코드가 이미 있으면 멈추고 `/jig:adopt` 를 권한다.
- git 저장소가 아니면 `git init -b main`.

## 2. 의도 묻기 (추측 금지)
사용자에게서 끌어낸다. 한 번에 4개 이하, 추천안을 먼저.
- 무엇을, 누구를 위해, 왜 — 핵심 시나리오 1~3개
- 하지 않는 것 (범위 경계)
- 품질 기준 중 측정 가능한 것
- 스택: 사용자가 정했으면 그대로. 안 정했으면 요구사항에 맞는 후보 2~3개를 장단점과 함께 제시하고 고르게 한다. 언어 숙련도가 아니라 요구사항이 기준이다.
- 배포 형태 (로컬 도구 / 서버 / 정적 사이트 …) — 모르면 "미정"으로 두고 열린 질문에 적는다.

## 3. 뼈대
- 스택의 **공식 생성기**로 뼈대를 만든다 (예: `uv init --package`, `pnpm create vite`, `go mod init`). 직접 템플릿을 짜지 않는다.
- 테스트 러너·린터를 설치하고, 빈 상태에서 테스트·린트 명령이 성공하는 것을 실행해서 확인한다.

## 4. 하네스 파일
| 대상 | 원본 | 채울 것 |
|---|---|---|
| `AGENTS.md` | `templates/AGENTS.md` | 스택, CRITICAL 규칙(아직 없으면 비밀값 규칙만), 실제 명령어 |
| `CLAUDE.md` | `templates/CLAUDE.md` | 그대로 |
| `jig.json` | `templates/jig-config.md` 의 예시 | 3단계에서 성공을 확인한 명령, 실제 디렉토리 구조에 맞는 `tdd` |
| `docs/PRD.md` | `templates/docs/PRD.md` | 2단계 답 |
| `docs/ARCHITECTURE.md` | `templates/docs/ARCHITECTURE.md` | 아는 만큼만. 모르는 절은 "미정 — 첫 spec 에서 정함" |
| `docs/adr/0001-stack.md` | `templates/docs/adr/0000-template.md` | 스택 결정과 대안 |
| `docs/GLOSSARY.md`, `docs/engineering-notes.md`, `docs/specs/README.md` | 같은 이름 템플릿 | 그대로 (용어는 PRD 에서 나온 것만) |
| `.github/` | `templates/.github/` | CI 의 `JIG:SETUP` 자리에 툴체인 설치 단계 |

`.gitignore` 에 스택 기본 항목이 있는지 확인한다.

## 5. 확인과 마무리
- `jig.json` 의 각 명령을 실행해 성공을 확인한다 (증거로 출력 요약을 보고).
- `jig.json` 이 막는지 확인: `tdd.source` 에 해당하는 가상의 경로 하나에 대해 기대 테스트 경로가 맞게 계산되는지 사용자에게 보여준다.
- 첫 커밋: `chore: bootstrap with jig`.
- 사용자에게 보고: 만든 파일, 정한 것, 열린 질문, 다음 단계 `/jig:spec <첫 기능>`.
