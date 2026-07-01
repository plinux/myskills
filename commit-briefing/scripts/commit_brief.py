#!/usr/bin/env python3
"""Generate commit briefing metrics from a git repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


CATEGORY_LABELS = {
    "feature": "特性",
    "bugfix": "Bugfix",
    "refactor": "重构",
    "test": "测试",
    "docs": "文档",
    "style": "样式",
    "performance": "性能",
    "security": "安全",
    "build": "构建/CI",
    "dependency": "依赖",
    "other": "其他",
}

PREFIX_CATEGORY = {
    "feature": "feature",
    "feat": "feature",
    "bugfix": "bugfix",
    "fix": "bugfix",
    "refactor": "refactor",
    "test": "test",
    "tests": "test",
    "docs": "docs",
    "doc": "docs",
    "style": "style",
    "perf": "performance",
    "performance": "performance",
    "security": "security",
    "build": "build",
    "ci": "build",
    "chore": "build",
    "deps": "dependency",
    "dependency": "dependency",
}

CODE_EXTS = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".py",
    ".rb",
    ".php",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".swift",
    ".scala",
    ".cs",
    ".sql",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".lua",
    ".r",
    ".pl",
    ".pm",
    ".dart",
    ".vue",
    ".svelte",
}

DOC_EXTS = {".md", ".rst", ".adoc", ".txt", ".org"}
CONFIG_EXTS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".properties",
    ".gradle",
    ".lock",
}
RESOURCE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".avif",
    ".bmp",
    ".tiff",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".mp4",
    ".mov",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".tar",
    ".pdf",
    ".pptx",
    ".docx",
    ".xlsx",
}

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|specs?|__tests__|testdata|fixtures)(/|$)|"
    r"(^|/).*(test|spec|_test|Test|Spec)\.(py|js|jsx|ts|tsx|go|java|kt|rb|php|rs|cpp|cc|cxx|c|h)$"
)
TEST_EVIDENCE_RE = re.compile(
    r"(?im)^\s*(Tested|Tests?|Verification|Verified|QA|Acceptance|CI|"
    r"测试|验证|验收)\s*[:：]\s*(.+)$"
)
COMMAND_RE = re.compile(
    r"(?i)\b(pytest|npm test|pnpm test|yarn test|go test|cargo test|mvn test|"
    r"gradle test|ctest|make test|jest|vitest|unittest)\b"
)
PASS_RE = re.compile(r"(?i)\b(pass(?:ed)?|ok|success|succeeded|green|通过|成功)\b")
FAIL_RE = re.compile(r"(?i)\b(fail(?:ed)?|error|failed|red|失败|未通过)\b")
COVERAGE_RE = re.compile(r"(?i)(coverage|覆盖率)[^0-9]{0,30}(\d+(?:\.\d+)?%)")


def run_git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def split_commit_format(raw: str) -> dict[str, str]:
    fields = raw.split("\x00", 5)
    if len(fields) < 6:
        raise RuntimeError("unexpected git show output")
    return {
        "hash": fields[0],
        "short_hash": fields[1],
        "date": fields[2],
        "author": fields[3],
        "subject": fields[4].strip(),
        "body": fields[5].strip(),
    }


def numeric(value: str) -> int | None:
    return int(value) if value.isdigit() else None


def classify_file(path_text: str) -> str:
    path = path_text.strip()
    lower = path.lower()
    suffix = Path(lower).suffix
    basename = Path(lower).name

    if TEST_PATH_RE.search(path):
        return "test"
    if suffix in RESOURCE_EXTS:
        return "resource"
    if suffix in DOC_EXTS or basename in {"readme", "license", "notice", "changelog"}:
        return "docs"
    if suffix in CONFIG_EXTS or lower.startswith(".github/") or lower.startswith(".gitlab/"):
        return "config"
    if suffix in CODE_EXTS or basename in {"makefile", "dockerfile", "rakefile"}:
        return "code"
    return "other"


def empty_bucket() -> dict[str, Any]:
    return {"files": 0, "added": 0, "deleted": 0, "binary_files": 0, "paths": []}


def add_numstat(bucket: dict[str, Any], added: int | None, deleted: int | None, path: str) -> None:
    bucket["files"] += 1
    bucket["paths"].append(path)
    if added is None or deleted is None:
        bucket["binary_files"] += 1
        return
    bucket["added"] += added
    bucket["deleted"] += deleted


def collect_stats(repo: Path, commit: str) -> dict[str, dict[str, Any]]:
    buckets = {
        "code": empty_bucket(),
        "test": empty_bucket(),
        "resource": empty_bucket(),
        "docs": empty_bucket(),
        "config": empty_bucket(),
        "other": empty_bucket(),
    }
    output = run_git(repo, ["show", "--numstat", "--format=", "--find-renames", commit])
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added = numeric(parts[0])
        deleted = numeric(parts[1])
        path = parts[-1]
        add_numstat(buckets[classify_file(path)], added, deleted, path)
    return buckets


def category_from_subject(subject: str, buckets: dict[str, dict[str, Any]]) -> str:
    bracket = re.match(r"^\[([A-Za-z-]+)\]", subject)
    if bracket:
        key = bracket.group(1).lower()
        if key in PREFIX_CATEGORY:
            return PREFIX_CATEGORY[key]

    conventional = re.match(r"^([a-zA-Z]+)(?:\([^)]+\))?!?:", subject)
    if conventional:
        key = conventional.group(1).lower()
        if key in PREFIX_CATEGORY:
            return PREFIX_CATEGORY[key]

    changed = {name for name, bucket in buckets.items() if bucket["files"]}
    if changed == {"test"}:
        return "test"
    if changed and changed <= {"docs"}:
        return "docs"
    if changed and changed <= {"config"}:
        return "build"
    return "other"


def extract_test_evidence(body: str) -> dict[str, Any] | None:
    evidence_lines = [match.group(0).strip() for match in TEST_EVIDENCE_RE.finditer(body)]
    command_hits = sorted(set(COMMAND_RE.findall(body)))
    if not evidence_lines and not command_hits:
        return None

    status = None
    if PASS_RE.search(body):
        status = "通过"
    if FAIL_RE.search(body):
        status = "失败"

    coverage = sorted({match.group(2) for match in COVERAGE_RE.finditer(body)})
    return {
        "evidence": evidence_lines,
        "commands": command_hits,
        "status": status,
        "coverage": coverage,
    }


def get_commits(repo: Path, rev_range: str | None) -> list[str]:
    if rev_range:
        if rev_range != "--all" and not any(token in rev_range for token in ("..", "^", " ")):
            commit = run_git(repo, ["rev-parse", "--verify", f"{rev_range}^{{commit}}"]).strip()
            return [commit]
        return [line.strip() for line in run_git(repo, ["rev-list", "--reverse", rev_range]).splitlines() if line.strip()]
    return [line.strip() for line in run_git(repo, ["rev-list", "--reverse", "--all"]).splitlines() if line.strip()]


def collect_commit(repo: Path, commit: str) -> dict[str, Any]:
    raw = run_git(
        repo,
        [
            "show",
            "--quiet",
            "--date=short",
            "--format=%H%x00%h%x00%ad%x00%an%x00%s%x00%b",
            commit,
        ],
    )
    info = split_commit_format(raw)
    buckets = collect_stats(repo, commit)
    category_key = category_from_subject(info["subject"], buckets)
    test_evidence = extract_test_evidence(info["body"])

    info.update(
        {
            "category": CATEGORY_LABELS[category_key],
            "category_key": category_key,
            "stats": buckets,
        }
    )
    if test_evidence:
        info["test_evidence"] = test_evidence
    return info


def summarize(commits: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "commits": len(commits),
        "categories": Counter(commit["category"] for commit in commits),
        "code_added": 0,
        "code_deleted": 0,
        "test_added": 0,
        "test_deleted": 0,
        "resource_files": 0,
        "commits_without_test_evidence": 0,
    }
    for commit in commits:
        code = commit["stats"]["code"]
        tests = commit["stats"]["test"]
        resources = commit["stats"]["resource"]
        totals["code_added"] += code["added"]
        totals["code_deleted"] += code["deleted"]
        totals["test_added"] += tests["added"]
        totals["test_deleted"] += tests["deleted"]
        totals["resource_files"] += resources["files"]
        if "test_evidence" not in commit:
            totals["commits_without_test_evidence"] += 1
    totals["categories"] = dict(totals["categories"])
    return totals


def format_change(bucket: dict[str, Any]) -> str:
    return f"+{bucket['added']}/-{bucket['deleted']}，{bucket['files']} 文件"


def format_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Commit 简报",
        "",
        f"- 范围：`{payload['range']}`",
        f"- 提交数：{payload['summary']['commits']}",
        f"- 代码总量：+{payload['summary']['code_added']}/-{payload['summary']['code_deleted']}",
        f"- 测试代码总量：+{payload['summary']['test_added']}/-{payload['summary']['test_deleted']}",
        f"- 资源文件数：{payload['summary']['resource_files']}",
        f"- 无测试证据提交数：{payload['summary']['commits_without_test_evidence']}",
        "",
        "## 分类统计",
        "",
    ]
    for category, count in sorted(payload["summary"]["categories"].items()):
        lines.append(f"- {category}: {count}")
    lines.extend(["", "## 提交明细", ""])

    for commit in payload["commits"]:
        stats = commit["stats"]
        resource_paths = stats["resource"]["paths"][:8]
        resource_text = "无"
        if resource_paths:
            suffixes = sorted({Path(path.lower()).suffix or "unknown" for path in resource_paths})
            resource_text = f"{stats['resource']['files']} 文件，类型 {', '.join(suffixes)}"

        lines.append(f"### `{commit['short_hash']}` {commit['subject']}")
        lines.append("")
        lines.append(f"- 分类：{commit['category']}")
        lines.append(f"- 代码量：{format_change(stats['code'])}")
        lines.append(f"- 测试代码量：{format_change(stats['test'])}")
        lines.append(f"- 资源变更：{resource_text}")
        other_parts = []
        for name, label in [("docs", "文档"), ("config", "配置"), ("other", "其他")]:
            bucket = stats[name]
            if bucket["files"]:
                other_parts.append(f"{label} {format_change(bucket)}")
        if other_parts:
            lines.append(f"- 其他变更：{'; '.join(other_parts)}")
        evidence = commit.get("test_evidence")
        if evidence:
            lines.append("- 测试验收证据：")
            for item in evidence.get("evidence", []):
                lines.append(f"  - {item}")
            if evidence.get("commands"):
                lines.append(f"  - 命令：{', '.join(evidence['commands'])}")
            if evidence.get("status"):
                lines.append(f"  - 是否通过：{evidence['status']}")
            if evidence.get("coverage"):
                lines.append(f"  - 覆盖率：{', '.join(evidence['coverage'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.getcwd(), help="Git repository path")
    parser.add_argument("--range", dest="rev_range", help="Git revision range or single commit")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    try:
        commits = [collect_commit(repo, commit) for commit in get_commits(repo, args.rev_range)]
        payload = {
            "repo": str(repo),
            "range": args.rev_range or "--all",
            "summary": summarize(commits),
            "commits": commits,
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_markdown(payload), end="")
    except Exception as exc:
        print(f"commit_brief.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
