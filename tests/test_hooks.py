"""hooks/jig_hooks.py 의 동작 명세.

훅은 스택을 모른다. 프로젝트 루트의 jig.json 만 읽고, 없으면 아무것도 하지 않는다.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "jig_hooks.py"

PY_CONFIG = {
    "commands": {"test": "python3 -c 'print(1)'"},
    "tdd": {
        "source": ["src/**/*.py"],
        "roots": ["src"],
        "tests": ["tests/{path}/test_{name}.py"],
        "exempt": ["**/__init__.py"],
    },
}


def run(cwd, mode, payload, codex=False):
    args = [sys.executable, str(HOOK), mode] + (["--codex"] if codex else [])
    return subprocess.run(
        args, input=json.dumps(payload), cwd=cwd, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin:" + str(Path(sys.executable).parent)},
    )


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "README.md").write_text("x")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def configure(repo, config):
    (repo / "jig.json").write_text(json.dumps(config))


def edit(repo, rel):
    return {"tool_name": "Write", "tool_input": {"file_path": str(repo / rel)}}


def decision(result):
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


# --- tdd ---------------------------------------------------------------------

def test_no_config_means_hooks_do_nothing(repo):
    assert decision(run(repo, "tdd", edit(repo, "src/app/core.py"))) is None
    r = run(repo, "verify", {})
    assert r.returncode == 0


def test_source_without_test_is_denied(repo):
    configure(repo, PY_CONFIG)
    r = run(repo, "tdd", edit(repo, "src/app/core.py"))
    assert decision(r) == "deny"
    assert "tests/app/test_core.py" in r.stdout


def test_source_with_test_is_allowed(repo):
    configure(repo, PY_CONFIG)
    (repo / "tests/app").mkdir(parents=True)
    (repo / "tests/app/test_core.py").write_text("")
    assert decision(run(repo, "tdd", edit(repo, "src/app/core.py"))) is None


@pytest.mark.parametrize("rel", ["tests/app/test_core.py", "src/app/__init__.py", "docs/a.md", "web/x.ts"])
def test_non_source_or_exempt_is_allowed(repo, rel):
    configure(repo, PY_CONFIG)
    assert decision(run(repo, "tdd", edit(repo, rel))) is None


def test_template_placeholders_dir_and_ext(repo):
    configure(repo, {"tdd": {"source": ["web/**/*.ts"], "tests": ["{dir}/{name}.test.{ext}"]}})
    assert decision(run(repo, "tdd", edit(repo, "web/lib/sum.ts"))) == "deny"
    (repo / "web/lib").mkdir(parents=True)
    (repo / "web/lib/sum.test.ts").write_text("")
    assert decision(run(repo, "tdd", edit(repo, "web/lib/sum.ts"))) is None


def test_codex_apply_patch_is_checked(repo):
    configure(repo, PY_CONFIG)
    patch = "*** Begin Patch\n*** Add File: src/app/core.py\n+x = 1\n*** End Patch"
    r = run(repo, "tdd", {"tool_name": "apply_patch", "tool_input": {"command": patch}}, codex=True)
    assert decision(r) == "deny"


def test_editing_jig_config_asks_user(repo):
    configure(repo, PY_CONFIG)
    assert decision(run(repo, "tdd", edit(repo, "jig.json"))) == "ask"


# --- bash --------------------------------------------------------------------

@pytest.mark.parametrize("cmd", ["rm -rf build", "git push --force origin main", "git reset --hard HEAD~1"])
def test_dangerous_bash_is_denied(repo, cmd):
    assert decision(run(repo, "bash", {"tool_input": {"command": cmd}})) == "deny"


def test_safe_bash_passes_and_codex_argv_is_joined(repo):
    assert decision(run(repo, "bash", {"tool_input": {"command": "ls -la"}})) is None
    r = run(repo, "bash", {"tool_input": {"command": ["rm", "-rf", "/tmp/x"]}}, codex=True)
    assert decision(r) == "deny"


# --- verify ------------------------------------------------------------------

def test_verify_skips_when_only_docs_changed(repo):
    configure(repo, {**PY_CONFIG, "commands": {"test": "false"}})
    git(repo, "add", "jig.json")
    git(repo, "commit", "-qm", "cfg")
    (repo / "README.md").write_text("changed")
    assert run(repo, "verify", {}).returncode == 0


def test_verify_reports_missing_test_and_failing_command(repo):
    configure(repo, {**PY_CONFIG, "commands": {"lint": "echo LINT-BROKEN && false"}})
    (repo / "src/app").mkdir(parents=True)
    (repo / "src/app/core.py").write_text("x = 1")
    r = run(repo, "verify", {})
    assert r.returncode == 2
    assert "src/app/core.py" in r.stderr
    assert "LINT-BROKEN" in r.stderr


def test_verify_codex_format_blocks_on_stdout(repo):
    configure(repo, {**PY_CONFIG, "commands": {"test": "false"}})
    (repo / "src").mkdir()
    (repo / "src/x.py").write_text("")
    r = run(repo, "verify", {}, codex=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)["decision"] == "block"


def test_verify_stop_hook_active_does_not_loop(repo):
    configure(repo, {**PY_CONFIG, "commands": {"test": "false"}})
    (repo / "src").mkdir()
    (repo / "src/x.py").write_text("")
    assert run(repo, "verify", {"stop_hook_active": True}).returncode == 0


def test_verify_runs_related_tests_only(repo):
    config = {**PY_CONFIG, "commands": {"test_files": "echo RAN {files} && false"}}
    configure(repo, config)
    (repo / "src/app").mkdir(parents=True)
    (repo / "src/app/core.py").write_text("")
    (repo / "tests/app").mkdir(parents=True)
    (repo / "tests/app/test_core.py").write_text("")
    r = run(repo, "verify", {})
    assert r.returncode == 2
    assert "RAN tests/app/test_core.py" in r.stderr


def test_verify_passes_and_is_not_rerun_after_commit(repo):
    configure(repo, PY_CONFIG)
    (repo / "src").mkdir()
    (repo / "src/x.py").write_text("")
    (repo / "tests").mkdir()
    (repo / "tests/test_x.py").write_text("")
    assert run(repo, "verify", {}).returncode == 0
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "work")
    configure(repo, {**PY_CONFIG, "commands": {"test": "false"}})
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "cfg")
    # 마지막 검증 이후 커밋에 바뀐 소스가 있으면 커밋됐어도 다시 검증한다
    assert run(repo, "verify", {}).returncode == 2


def test_codex_patch_text_is_not_treated_as_shell(repo):
    patch = "*** Begin Patch\n*** Add File: scripts/clean.sh\n+rm -rf build\n*** End Patch"
    r = run(repo, "bash", {"tool_name": "apply_patch", "tool_input": {"command": patch}}, codex=True)
    assert decision(r) is None
