from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)
ANSI_GREEN = "\033[32m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"


@dataclass(frozen=True)
class FileCoverage:
    executed_lines: frozenset[int]
    missing_lines: frozenset[int]
    excluded_lines: frozenset[int]

    def marker_for(self, line_no: int) -> str:
        if line_no in self.executed_lines:
            return "o"
        if line_no in self.missing_lines:
            return "x"
        if line_no in self.excluded_lines:
            return "-"
        return " "


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Annotate added diff lines with coverage status."
    )
    parser.add_argument(
        "revspec",
        nargs="?",
        help=(
            "Git revision range passed to git diff, for example "
            "'HEAD~1...HEAD' or '<commit>..<commit>'."
        ),
    )
    parser.add_argument(
        "--coverage-json",
        default="coverage.json",
        help="Path to coverage.py JSON output. Default: coverage.json",
    )
    parser.add_argument(
        "--diff-file",
        help="Read unified diff from a file instead of running git diff. Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--unstaged",
        action="store_true",
        help="Diff unstaged working tree changes (runs 'git diff -- <pathspec>').",
    )
    parser.add_argument(
        "--base",
        default="master",
        help=(
            "Base ref for git diff when revspec and --diff-file are not used. "
            "Default: master"
        ),
    )
    parser.add_argument(
        "--target",
        default="HEAD",
        help=(
            "Target ref for git diff when revspec and --diff-file are not used. "
            "Default: HEAD"
        ),
    )
    parser.add_argument(
        "--pathspec",
        nargs="*",
        default=["src/"],
        help="Pathspec passed to git diff. Default: src/",
    )
    return parser.parse_args()


def load_coverage(path: str) -> dict[str, FileCoverage]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)

    files = payload.get("files", {})
    coverage_by_path: dict[str, FileCoverage] = {}
    for raw_path, entry in files.items():
        coverage_by_path[normalize_path(raw_path)] = FileCoverage(
            executed_lines=frozenset(entry.get("executed_lines", [])),
            missing_lines=frozenset(entry.get("missing_lines", [])),
            excluded_lines=frozenset(entry.get("excluded_lines", [])),
        )
    return coverage_by_path


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith(("a/", "b/")):
        normalized = normalized[2:]

    parts = PurePosixPath(normalized).parts
    for anchor in ("src", "tests"):
        if anchor in parts:
            normalized = str(PurePosixPath(*parts[parts.index(anchor) :]))
            break
    else:
        normalized = str(PurePosixPath(normalized))

    return normalized.casefold()


def read_diff(args: argparse.Namespace) -> str:
    if args.diff_file:
        if args.diff_file == "-":
            return sys.stdin.read()
        with open(args.diff_file, encoding="utf-8") as handle:
            return handle.read()

    if args.unstaged:
        command = ["git", "diff", "--", *args.pathspec]
    else:
        revspec = args.revspec or f"{args.base}...{args.target}"
        command = [
            "git",
            "diff",
            revspec,
            "--",
            *args.pathspec,
        ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def resolve_coverage(
    diff_path: str,
    coverage_by_path: dict[str, FileCoverage],
) -> FileCoverage | None:
    normalized_diff_path = normalize_path(diff_path)
    if normalized_diff_path in coverage_by_path:
        return coverage_by_path[normalized_diff_path]

    suffix = f"/{normalized_diff_path}"
    matches = [
        coverage
        for path, coverage in coverage_by_path.items()
        if path.endswith(suffix) or normalized_diff_path.endswith(f"/{path}")
    ]
    if len(matches) == 1:
        return matches[0]
    return None


def annotate_diff(diff_text: str, coverage_by_path: dict[str, FileCoverage]) -> str:
    output_lines: list[str] = []
    current_coverage: FileCoverage | None = None
    new_line_no: int | None = None

    for raw_line in split_preserving_newlines(diff_text):
        line = raw_line.rstrip("\n")

        if line.startswith("+++ "):
            diff_path = line[4:].strip()
            current_coverage = None if diff_path == "/dev/null" else resolve_coverage(
                diff_path, coverage_by_path
            )
            output_lines.append(raw_line)
            continue

        if line.startswith("@@ "):
            match = HUNK_HEADER_RE.match(line)
            if not match:
                raise ValueError(f"Invalid hunk header: {line}")
            new_line_no = int(match.group("new_start"))
            output_lines.append(raw_line)
            continue

        if line.startswith("+") and not line.startswith("+++ "):
            if new_line_no is None:
                raise ValueError("Added line encountered outside a hunk.")
            marker = "?" if current_coverage is None else current_coverage.marker_for(
                new_line_no
            )
            payload = line[1:]
            annotated = f"+ [{marker}] {payload}".rstrip()
            output_lines.append(f"{annotated}\n")
            new_line_no += 1
            continue

        if line.startswith("-") and not line.startswith("--- "):
            output_lines.append(raw_line)
            continue

        if line.startswith("\\"):
            output_lines.append(raw_line)
            continue

        if line.startswith(" ") and new_line_no is not None:
            new_line_no += 1

        output_lines.append(raw_line)

    return "".join(output_lines)


def split_preserving_newlines(text: str) -> Iterable[str]:
    return text.splitlines(keepends=True)


def colorize_annotated_line(marker: str, annotated_line: str) -> str:
    if marker in {"o", " "}:
        return f"{ANSI_GREEN}{annotated_line}{ANSI_RESET}"
    if marker == "x":
        return f"{ANSI_RED}{annotated_line}{ANSI_RESET}"
    return annotated_line


def main() -> int:
    args = parse_args()
    coverage_by_path = load_coverage(args.coverage_json)
    diff_text = read_diff(args)
    annotated_diff = annotate_diff(diff_text, coverage_by_path)
    colored_lines: list[str] = []
    for raw_line in split_preserving_newlines(annotated_diff):
        line = raw_line.rstrip("\n")
        if line.startswith("+ [") and len(line) >= 4:
            marker = line[3]
            colored_lines.append(colorize_annotated_line(marker, line) + "\n")
            continue
        colored_lines.append(raw_line)
    output = "".join(colored_lines)
    sys.stdout.buffer.write(output.encode("utf-8", errors="replace"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
