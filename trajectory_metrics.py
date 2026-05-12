#!/usr/bin/env python3
"""
trajectory_metrics.py — Compute message-count metrics from a mini-SWE-agent-v2 trajectory.

The trajectory JSON is expected to contain a top-level "messages" array where
every element has at least a "role" field with one of the values:
  system | user | assistant | tool

Usage
-----
    python trajectory_metrics.py <path-to-trajectory.json>
    python trajectory_metrics.py <path-to-trajectory.json> [<path2> ...]
    python trajectory_metrics.py --help
"""

import argparse
import json
import sys
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class MessageCounts(NamedTuple):
    system: int
    user: int
    assistant: int
    tool: int

    @property
    def total(self) -> int:
        return self.system + self.user + self.assistant + self.tool


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

KNOWN_ROLES = {"system", "user", "assistant", "tool"}


def load_trajectory(path: Path) -> dict:
    """Load and return the JSON trajectory from *path*."""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise SystemExit(f"Error: file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: {path} is not valid JSON — {exc}")


def extract_messages(data: dict) -> list[dict]:
    """
    Return the list of message objects from the trajectory.

    Supports:
      - { "messages": [...] }
      - { "trajectory": [...] }
      - nested wrapper objects, such as Docent-downloaded runs
    """

    def looks_like_messages(value: object) -> bool:
        return (
            isinstance(value, list)
            and len(value) > 0
            and all(isinstance(item, dict) for item in value)
            and any("role" in item for item in value)
        )

    def search(obj: object) -> list[dict] | None:
        if isinstance(obj, dict):
            messages = obj.get("messages")
            if looks_like_messages(messages):
                return messages

            trajectory = obj.get("trajectory")
            if isinstance(trajectory, list):
                flattened: list[dict] = []

                for step in trajectory:
                    if isinstance(step, dict):
                        step_messages = step.get("messages")
                        if looks_like_messages(step_messages):
                            flattened.extend(step_messages)
                        elif "role" in step:
                            flattened.append(step)

                if flattened:
                    return flattened

            for value in obj.values():
                found = search(value)
                if found:
                    return found

        elif isinstance(obj, list):
            if looks_like_messages(obj):
                return obj

            for value in obj:
                found = search(value)
                if found:
                    return found

        return None

    found = search(data)

    if found:
        return found

    raise SystemExit(
        "Error: cannot locate a messages array in the trajectory JSON.\n"
        "Expected a list of message objects containing role fields."
    )


def count_messages(messages: list[dict]) -> tuple[MessageCounts, dict[str, int]]:
    """
    Count messages by role.

    Returns
    -------
    counts : MessageCounts
        Counts for the four canonical roles.
    unknown : dict[str, int]
        Counts for any unrecognised roles (for diagnostics).
    """
    counts: dict[str, int] = {role: 0 for role in KNOWN_ROLES}
    unknown: dict[str, int] = {}

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "")).lower()
        if role in KNOWN_ROLES:
            counts[role] += 1
        else:
            unknown[role] = unknown.get(role, 0) + 1

    return (
        MessageCounts(
            system=counts["system"],
            user=counts["user"],
            assistant=counts["assistant"],
            tool=counts["tool"],
        ),
        unknown,
    )


# ---------------------------------------------------------------------------
# Formatting / output
# ---------------------------------------------------------------------------

def format_report(counts: MessageCounts, unknown: dict[str, int], label: str | None = None) -> str:
    """Render the metrics as a human-readable string."""
    lines: list[str] = []

    if label:
        lines.append(f"File: {label}")
        lines.append("")

    width = max(len(str(counts.total)), 2)

    def row(name: str, value: int) -> str:
        return f"{name:<20} {value:>{width}}"

    lines.append(row("System messages:", counts.system))
    lines.append(row("User messages:", counts.user))
    lines.append(row("Assistant messages:", counts.assistant))
    lines.append(row("Tool messages:", counts.tool))

    if unknown:
        for role, n in sorted(unknown.items()):
            display = role if role else "<empty>"
            lines.append(row(f"  [{display}] messages:", n))

    sep_len = 20 + 1 + width
    lines.append("=" * sep_len)
    lines.append(row("Total messages:", counts.total))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trajectory_metrics",
        description=(
            "Compute message-count metrics from a mini-SWE-agent-v2 trajectory JSON file.\n\n"
            "The tool reads the 'messages' array from the JSON and tallies how many messages\n"
            "belong to each role: system, user, assistant, tool."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python trajectory_metrics.py run.json\n"
            "  python trajectory_metrics.py traj1.json traj2.json traj3.json\n"
            "  python trajectory_metrics.py ./trajectories/*.json\n"
            "  cat run.json | python trajectory_metrics.py -   # read from stdin"
        ),
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        help="Path(s) to trajectory JSON file(s). Use '-' to read from stdin.",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        default=False,
        help="Output results as JSON (useful for scripting).",
    )
    return parser


def process_file(path_or_stdin: str) -> tuple[str, MessageCounts, dict[str, int]]:
    """Load and analyse one trajectory file. Returns (label, counts, unknown)."""
    if path_or_stdin == "-":
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Error: stdin is not valid JSON — {exc}")
        label = "<stdin>"
    else:
        p = Path(path_or_stdin)
        data = load_trajectory(p)
        label = str(p)

    messages = extract_messages(data)
    counts, unknown = count_messages(messages)
    return label, counts, unknown


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    results = []
    for file_arg in args.files:
        label, counts, unknown = process_file(file_arg)
        results.append((label, counts, unknown))

    if args.output_json:
        output = []
        for label, counts, unknown in results:
            entry = {
                "file": label,
                "system": counts.system,
                "user": counts.user,
                "assistant": counts.assistant,
                "tool": counts.tool,
                "total": counts.total,
            }
            if unknown:
                entry["unknown"] = unknown
            output.append(entry)
        print(json.dumps(output if len(output) > 1 else output[0], indent=2))
        return

    separator = "\n" + "-" * 40 + "\n"
    parts = [
        format_report(counts, unknown, label if len(results) > 1 else None)
        for label, counts, unknown in results
    ]
    print(separator.join(parts))


if __name__ == "__main__":
    main()
