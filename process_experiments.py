"""
Task 2 aggregation script.

This script processes all downloaded mini-SWE-agent-v2 trajectories by reusing
the Task 1 command-line tool implementation in trajectory_metrics.py.

Expected layout:

    experiments_for_task2/
      claude-4-5-opus-high/
        run1.json
        run2.json
      gemini-3-flash-high/
        run1.json
      minimax-2-5-high/
        run1.json
      claude-4-6-opus/
        run1.json
      gpt-5-2-codex/
        run1.json

Outputs:

    task2_per_run.csv
    task2_summary.csv
    task2_summary.md
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from trajectory_metrics import process_file


def find_trajectory_files(root: Path) -> list[Path]:
    """Return all JSON and .traj trajectory files under root."""
    files: list[Path] = []
    files.extend(root.rglob("*.json"))
    files.extend(root.rglob("*.traj"))
    return sorted(files)


def model_name_for_file(root: Path, file_path: Path) -> str:
    """
    Infer the model name from the first folder below the experiments root.

    Example:
        experiments_for_task2/claude-4-5-opus-high/abc.json
        -> claude-4-5-opus-high
    """
    relative = file_path.relative_to(root)
    if len(relative.parts) >= 2:
        return relative.parts[0]
    return "unknown"


def write_per_run_csv(rows: list[dict], output_path: Path) -> None:
    """Write one metrics row per trajectory."""
    fieldnames = [
        "model",
        "file",
        "system",
        "user",
        "assistant",
        "tool",
        "total",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: list[dict]) -> list[dict]:
    """Aggregate per-run metrics into one summary row per model."""
    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        grouped[row["model"]].append(row)

    summary: list[dict] = []

    for model, model_rows in sorted(grouped.items()):
        totals = [row["total"] for row in model_rows]
        systems = [row["system"] for row in model_rows]
        users = [row["user"] for row in model_rows]
        assistants = [row["assistant"] for row in model_rows]
        tools = [row["tool"] for row in model_rows]

        summary.append(
            {
                "model": model,
                "runs": len(model_rows),
                "avg_total": round(mean(totals), 2),
                "avg_system": round(mean(systems), 2),
                "avg_user": round(mean(users), 2),
                "avg_assistant": round(mean(assistants), 2),
                "avg_tool": round(mean(tools), 2),
                "min_total": min(totals),
                "max_total": max(totals),
            }
        )

    return summary


def write_summary_csv(summary: list[dict], output_path: Path) -> None:
    """Write the per-model summary as CSV."""
    fieldnames = [
        "model",
        "runs",
        "avg_total",
        "avg_system",
        "avg_user",
        "avg_assistant",
        "avg_tool",
        "min_total",
        "max_total",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)


def write_summary_markdown(summary: list[dict], output_path: Path) -> None:
    """Write the per-model summary as a Markdown table."""
    lines = [
        "# Task 2 Metrics Summary",
        "",
        "| Model | Runs | Avg total | Avg system | Avg user | Avg assistant | Avg tool | Min | Max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary:
        lines.append(
            f"| {row['model']} "
            f"| {row['runs']} "
            f"| {row['avg_total']} "
            f"| {row['avg_system']} "
            f"| {row['avg_user']} "
            f"| {row['avg_assistant']} "
            f"| {row['avg_tool']} "
            f"| {row['min_total']} "
            f"| {row['max_total']} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(summary: list[dict]) -> None:
    """Print a compact model-level summary to the terminal."""
    print("Task 2 model-level summary")
    print("=" * 80)
    print(
        f"{'Model':<35} {'Runs':>6} {'Avg total':>10} "
        f"{'Avg assistant':>14} {'Avg tool':>10} {'Min':>6} {'Max':>6}"
    )
    print("-" * 80)

    for row in summary:
        print(
            f"{row['model']:<35} "
            f"{row['runs']:>6} "
            f"{row['avg_total']:>10} "
            f"{row['avg_assistant']:>14} "
            f"{row['avg_tool']:>10} "
            f"{row['min_total']:>6} "
            f"{row['max_total']:>6}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Process all downloaded mini-SWE-agent-v2 trajectories using "
            "the Task 1 tool implementation from trajectory_metrics.py."
        )
    )
    parser.add_argument(
        "experiments_dir",
        help="Folder containing one subfolder per model.",
    )
    parser.add_argument(
        "--per-run",
        default="task2_per_run.csv",
        help="Path for per-trajectory CSV output.",
    )
    parser.add_argument(
        "--summary",
        default="task2_summary.csv",
        help="Path for per-model CSV summary output.",
    )
    parser.add_argument(
        "--markdown",
        default="task2_summary.md",
        help="Path for per-model Markdown summary output.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    root = Path(args.experiments_dir)

    if not root.exists():
        raise SystemExit(f"Error: folder does not exist: {root}")

    files = find_trajectory_files(root)

    if not files:
        raise SystemExit(f"Error: no .json or .traj files found under: {root}")

    rows: list[dict] = []
    failed: list[tuple[Path, str]] = []

    for file_path in files:
        try:
            label, counts, unknown = process_file(str(file_path))

            if unknown:
                print(f"Warning: {file_path} contains unknown roles: {unknown}")

            rows.append(
                {
                    "model": model_name_for_file(root, file_path),
                    "file": label,
                    "system": counts.system,
                    "user": counts.user,
                    "assistant": counts.assistant,
                    "tool": counts.tool,
                    "total": counts.total,
                }
            )

        except SystemExit as exc:
            failed.append((file_path, str(exc)))

    if not rows:
        raise SystemExit("Error: no valid trajectories were processed.")

    summary = build_summary(rows)

    write_per_run_csv(rows, Path(args.per_run))
    write_summary_csv(summary, Path(args.summary))
    write_summary_markdown(summary, Path(args.markdown))

    print_summary(summary)
    print()
    print("Saved:")
    print(f"- {args.per_run}")
    print(f"- {args.summary}")
    print(f"- {args.markdown}")

    if failed:
        print()
        print("Warnings: some files were skipped:")
        for path, error in failed:
            print(f"- {path}: {error}")


if __name__ == "__main__":
    main()
