# Task 2 Report: Trajectory Analysis of Top-5 mini-SWE-agent-v2 Models

## Data & Method

All 500 trajectories per model were downloaded from the Docent/SWEbench platform for the five top-ranked models on the mini-SWE-agent-v2 leaderboard: Claude 4.5 Opus (high reasoning), Gemini 3 Flash (high reasoning), MiniMax M2.5 (high reasoning), Claude Opus 4.6, and GPT-5-2-Codex. Message counts were computed using the `trajectory_metrics.py` tool and aggregated with `process_experiments.py`.

| Model | Runs | Avg total | Avg assistant | Avg tool | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| claude-4-5-opus-high | 500 | 72.41 | 32.89 | 37.51 | 14 | 222 |
| claude-4-6-opus | 500 | 60.84 | 28.93 | 29.91 | 11 | 288 |
| gemini-3-flash-high | 500 | 113.24 | 56.11 | 55.12 | 2 | 319 |
| gpt-5-2-codex | 500 | 72.88 | 35.04 | 35.84 | 17 | 251 |
| minimax-2-5-high | 500 | 121.89 | 60.44 | 59.44 | 23 | 502 |

Every trajectory had exactly 1 system message and 1 user message, as expected: the agent receives a single task prompt and operates autonomously from there.

## Observations

**MiniMax and Gemini use far more turns.** MiniMax M2.5 averages 121.89 messages per run — nearly double Claude Opus 4.6's 60.84. Gemini 3 Flash is similar at 113.24. This suggests these models issue more granular tool calls rather than batching work into longer assistant responses. Whether this reflects a different prompting strategy or a tendency toward shorter, more iterative steps is worth investigating.

**Claude Opus 4.6 is the most concise.** With an average of 60.84 total messages and the lowest assistant-message count (28.93), Claude 4.6 Opus resolves tasks with the fewest turns. This could indicate more efficient planning — doing more per step — or that it attempts less before concluding.

**Tool and assistant messages are nearly balanced for all models.** Across every model the ratio of assistant to tool messages stays close to 1:1 (e.g. 32.89 : 37.51 for Claude 4.5 Opus; 60.44 : 59.44 for MiniMax). This is structurally expected — each tool call generates one tool-result message — but confirms the trajectories follow a clean request/response pattern with minimal multi-tool batching per turn.

**High variance across runs is universal.** All models show large spreads between their minimum and maximum totals. Claude 4.6 Opus spans 11–288 messages; MiniMax spans 23–502. This variance likely reflects genuine task difficulty rather than model inconsistency: some SWE-bench issues require many exploratory steps while others are resolved quickly. The outlier maximum for MiniMax (502 messages) is notable and may indicate runs where the model entered a repetitive loop.

**The "high reasoning" label doesn't mean more messages.** Claude 4.5 Opus (high reasoning) averages only 72.41 messages — comparable to GPT-5-2-Codex at 72.88 — suggesting that extended thinking is happening within individual messages rather than producing more turns.
