#!/usr/bin/env python3
"""Codex 전역 훅(~/.codex/hooks.json)에 jig 훅을 등록한다. 여러 번 실행해도 한 번만 들어간다.

Codex 는 모든 도구 호출에 훅을 걸고(matcher 없음) 편집을 apply_patch 로 하므로, jig_hooks.py 를 --codex 로 부른다.
jig.json 이 없는 프로젝트에서는 tdd·verify 가 아무것도 하지 않으므로 전역 등록해도 다른 프로젝트에 영향이 없다.

사용: python3 codex/install-hooks.py [--dry-run] [--uninstall]
"""

import json
import shutil
import sys
from pathlib import Path

HOOKS = Path.home() / ".codex" / "hooks.json"
SCRIPT = (Path(__file__).resolve().parent.parent / "hooks" / "jig_hooks.py").as_posix()
TAG = "jig-hook"
ENTRIES = {
    "PreToolUse": [f'python3 "{SCRIPT}" tdd --codex', f'python3 "{SCRIPT}" bash --codex'],
    "Stop": [f'python3 "{SCRIPT}" verify --codex'],
}


def strip_jig(groups):
    kept = []
    for g in groups:
        hooks = [h for h in g.get("hooks", []) if h.get("statusMessage") != TAG]
        if hooks:
            kept.append({**g, "hooks": hooks})
    return kept


def main():
    dry = "--dry-run" in sys.argv
    data = json.loads(HOOKS.read_text()) if HOOKS.exists() else {"hooks": {}}
    hooks = data.setdefault("hooks", {})
    for event in ENTRIES:
        hooks[event] = strip_jig(hooks.get(event, []))
    if "--uninstall" not in sys.argv:
        for event, cmds in ENTRIES.items():
            for cmd in cmds:
                hooks[event].append({"hooks": [{"type": "command", "command": cmd, "timeout": 600, "statusMessage": TAG}]})
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry:
        print(text)
        return
    if HOOKS.exists():
        shutil.copy2(HOOKS, HOOKS.with_suffix(".json.bak-jig"))
    HOOKS.parent.mkdir(parents=True, exist_ok=True)
    HOOKS.write_text(text)
    print(f"updated {HOOKS} (backup: {HOOKS.with_suffix('.json.bak-jig')})")


if __name__ == "__main__":
    main()
