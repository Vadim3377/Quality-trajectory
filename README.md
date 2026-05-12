# Quality-trajectory

Internship application — Tasks 1 & 2.

Analyzes execution trajectories from the [mini-SWE-agent-v2](https://swebench.com/) leaderboard by counting messages per role (system / user / assistant / tool) across the top five models.

---

## Repository contents

| File | Description |
|---|---|
| `trajectory_metrics.py` | **Task 1** — CLI tool: parses a trajectory JSON and prints message counts |
| `main.py` | Downloads all runs for the five models from the Docent platform |
| `process_experiments.py` | **Task 2** — Batch-processes all downloaded trajectories and writes CSV/Markdown output |
| `sample_run.json` | Example trajectory file (Django bug-fix run) |
| `task2_per_run.csv` | Per-trajectory metrics (500 runs × 5 models) |
| `task2_summary.csv` | Per-model aggregated statistics |
| `task2_summary.md` | Same summary as a Markdown table |
| `report.md` | **Task 2 written report** — observations and findings |

---

## Task 1 — trajectory_metrics.py

Parses a mini-SWE-agent-v2 trajectory JSON and counts messages by role.

### Requirements

```bash
pip install docent-sdk   # only needed for main.py (downloading)
# trajectory_metrics.py and process_experiments.py use the standard library only
```

### Usage

```bash
# Single file
python trajectory_metrics.py sample_run.json

# Multiple files
python trajectory_metrics.py traj1.json traj2.json traj3.json

# Glob
python trajectory_metrics.py ./experiments_for_task2/claude-4-6-opus/*.json

# Read from stdin
cat sample_run.json | python trajectory_metrics.py -

# JSON output (useful for scripting)
python trajectory_metrics.py sample_run.json --json
```

### Example output

```
System messages:      1
User messages:        1
Assistant messages:  10
Tool messages:       10
=========================
Total messages:      22
```

---

## Task 2 — Processing the top-5 models

### Step 1 — Download trajectories

```bash
python main.py
```

This creates `experiments_for_task2/<model-name>/<run-id>.json` for all five models. Requires a Docent API connection.

### Step 2 — Compute metrics

```bash
python process_experiments.py experiments_for_task2
```

Outputs:

- `task2_per_run.csv` — one row per trajectory
- `task2_summary.csv` — one row per model
- `task2_summary.md` — Markdown table

See [`report.md`](report.md) for the full analysis and findings.
