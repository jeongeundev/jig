#!/usr/bin/env python3
"""jig 훅 — 스택을 모르는 TDD 가드, 위험 명령 차단, 턴 종료 검증.

사용: jig_hooks.py <tdd|bash|verify> [--codex]
  tdd     PreToolUse(Edit|Write, Codex apply_patch): 테스트 없는 소스 작성을 막고, jig.json 수정은 사용자에게 묻는다.
  bash    PreToolUse(Bash): 되돌리기 어려운 명령을 막는다.
  verify  Stop: 바뀐 소스에 테스트가 있는지 확인하고 jig.json 의 commands 를 실행한다.

스택별 정보는 전부 프로젝트 루트의 jig.json 에 있다. jig.json 이 없는 프로젝트에서는 tdd·verify 가 아무것도 하지 않는다.
표준 라이브러리만 쓴다.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG = "jig.json"
DANGEROUS = [
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r",
    r"\bgit\s+push\b.*(--force\b|\s-f\b)",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-zA-Z]*f",
    r"\bDROP\s+(TABLE|DATABASE)\b",
]
DOC_PATTERNS = ["*.md", "docs/**"]


# --- 공통 ---------------------------------------------------------------------

def project_root():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(out.stdout.strip()).resolve() if out.returncode == 0 else Path.cwd().resolve()


def load_config(root):
    path = root / CONFIG
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def match_any(rel, patterns):
    # fnmatch 의 * 는 / 도 넘으므로 "src/**/*.py" 가 src/x.py 와 src/a/b/x.py 를 모두 잡도록 ** 를 보정한다
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel, p.replace("**/", "")) for p in patterns)


def pretool(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}},
        ensure_ascii=False))


def command_text(tool_input):
    cmd = tool_input.get("command", "")
    return " ".join(cmd) if isinstance(cmd, list) else str(cmd)


# --- tdd ----------------------------------------------------------------------

def is_test_file(rel):
    name = Path(rel).name
    parts = Path(rel).parts
    return (bool(re.match(r"(test_.*|.*_test\.\w+|.*\.(test|spec)\.\w+)$", name))
            or any(p in ("tests", "test", "__tests__", "spec") for p in parts[:-1]))


def expected_tests(rel, tdd):
    p = Path(rel)
    dir_ = p.parent.as_posix()
    dir_ = "" if dir_ == "." else dir_
    path = dir_
    for r in tdd.get("roots", []):
        r = r.rstrip("/")
        if path == r:
            path = ""
            break
        if path.startswith(r + "/"):
            path = path[len(r) + 1:]
            break
    values = {"dir": dir_, "path": path, "name": p.stem, "ext": p.suffix.lstrip(".")}
    out = []
    for t in tdd.get("tests", []):
        s = t.format(**values)
        out.append(re.sub(r"/+", "/", s).lstrip("/"))
    return out


def missing_test(rel, root, config):
    """테스트가 필요한데 없으면 기대 경로 목록을, 아니면 None 을 돌려준다."""
    tdd = (config or {}).get("tdd")
    if not tdd or is_test_file(rel):
        return None
    if not match_any(rel, tdd.get("source", [])) or match_any(rel, tdd.get("exempt", [])):
        return None
    candidates = expected_tests(rel, tdd)
    if any((root / c).exists() for c in candidates):
        return None
    return candidates


def edited_files(payload, root):
    tool_input = payload.get("tool_input") or {}
    files = []
    if tool_input.get("file_path"):
        files.append(tool_input["file_path"])
    else:
        patch = command_text(tool_input)
        files += re.findall(r"^\*\*\* (?:Add|Update) File: (.+)$", patch, re.M)
    rels = []
    for f in files:
        p = Path(f)
        p = p if p.is_absolute() else root / p
        try:
            rels.append(p.resolve().relative_to(root).as_posix())
        except ValueError:
            continue  # 프로젝트 밖 파일은 판단하지 않는다
    return rels


def cmd_tdd(payload, codex):
    root = project_root()
    config = load_config(root)
    if config is None:
        return 0
    for rel in edited_files(payload, root):
        if rel == CONFIG:
            pretool("ask", "jig.json 은 검증 기준이다. 에이전트가 바꾸면 검증을 스스로 약하게 만들 수 있으므로 사용자 승인이 필요하다.")
            return 0
        missing = missing_test(rel, root, config)
        if missing:
            pretool("deny", f"JIG TDD: '{rel}' 의 테스트가 없다. 구현 전에 테스트를 먼저 작성하라. 기대 위치: {', '.join(missing)}")
            return 0
    return 0


# --- bash ---------------------------------------------------------------------

def cmd_bash(payload, codex):
    cmd = command_text(payload.get("tool_input") or {})
    if cmd.lstrip().startswith("*** Begin Patch"):
        return 0  # Codex apply_patch: 파일 내용이지 실행할 명령이 아니다
    for pattern in DANGEROUS:
        if re.search(pattern, cmd, re.I):
            pretool("deny", f"JIG: 되돌리기 어려운 명령이라 막았다 ({cmd[:80]}). 꼭 필요하면 사용자에게 직접 실행을 요청하라.")
            return 0
    return 0


# --- verify -------------------------------------------------------------------

def git_lines(root, *args):
    out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []


def changed_files(root, marker):
    files = set(git_lines(root, "diff", "--name-only", "HEAD"))
    files |= set(git_lines(root, "ls-files", "--others", "--exclude-standard"))
    head = (git_lines(root, "rev-parse", "HEAD") or [""])[0]
    prev = marker.read_text().strip() if marker.exists() else ""
    # 세션이 커밋하고 턴을 끝내도 빠지지 않도록, 마지막으로 통과한 커밋 이후의 커밋도 본다
    if prev and head and prev != head and git_lines(root, "cat-file", "-t", prev):
        files |= set(git_lines(root, "diff", "--name-only", prev, head))
    return sorted(f for f in files if (root / f).exists()), head


def run_shell(root, label, cmd):
    r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return f"\n===== {label} 실패: {cmd} =====\n{(r.stdout + r.stderr)[-4000:]}"
    return ""


def cmd_verify(payload, codex):
    if payload.get("stop_hook_active"):
        return 0
    root = project_root()
    config = load_config(root)
    if config is None:
        return 0
    git_dir = (git_lines(root, "rev-parse", "--absolute-git-dir") or [None])[0]
    if not git_dir:
        return 0
    marker = Path(git_dir) / "jig-verified"
    changed, head = changed_files(root, marker)
    code = [f for f in changed if not match_any(f, DOC_PATTERNS)]

    failed = ""
    if code:
        missing = [f for f in code if missing_test(f, root, config)]
        if missing:
            failed += "\n===== TDD 위반: 테스트 없는 소스 =====\n" + "\n".join(f"  - {f}" for f in missing)
        commands = config.get("commands", {})
        tests = sorted({t for f in code for t in ([f] if is_test_file(f) else expected_tests(f, config.get("tdd", {})))
                        if (root / t).exists() and is_test_file(t)})
        if commands.get("test_files") and tests:
            failed += run_shell(root, "관련 테스트", commands["test_files"].replace("{files}", " ".join(map(shlex.quote, tests))))
        elif commands.get("test"):
            failed += run_shell(root, "테스트", commands["test"])
        for key in ("lint", "typecheck"):
            if commands.get(key):
                failed += run_shell(root, key, commands[key])

    if failed:
        msg = "JIG 검증 실패 — 아래를 고친 뒤 턴을 끝내라." + failed
        if codex:
            print(json.dumps({"decision": "block", "reason": msg}, ensure_ascii=False))
            return 0
        print(msg, file=sys.stderr)
        return 2
    if head:
        marker.write_text(head)
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    codex = "--codex" in sys.argv
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    handler = {"tdd": cmd_tdd, "bash": cmd_bash, "verify": cmd_verify}.get(mode)
    if handler is None:
        print(__doc__, file=sys.stderr)
        return 1
    return handler(payload, codex)


if __name__ == "__main__":
    sys.exit(main())
