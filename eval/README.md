# Evaluation: how often does the AI get it right?

A fixed set of typical engineer requests (`requests.json`), each with an expected answer
from real simulation data and a pass rule. Running the same set after every change shows
whether answers got better or worse, and the failures show what to improve next.

## Request categories (43 requests)

| Category | What it tests | # |
|---|---|---|
| Discovery | Finding models, signals and settings | 5 |
| Run | Starting simulations, guardrails | 5 |
| Read values | Correct numbers in readable units | 11 |
| Reasoning | Engineering conclusions backed by data | 5 |
| Plot | Right signals in the chart | 5 |
| Compare | Using the right runs | 3 |
| Errors | Unknown models/signals, out-of-range requests | 5 |
| Ambiguous | Asking or stating assumptions instead of guessing | 4 |

Ground truth comes from run `20261107-203529_MBEV` (MBEV, one NEDC, 1180 s) unless the
request creates a new run; then the new run's own data is the reference.

## Scoring

Each request gets one result:

- **Pass**: meets the `pass_if` rule; every number traceable to a tool result.
- **Partial**: right approach, but a small error (rounding outside tolerance, missing unit, unclear sign).
- **Fail**: wrong signal, wrong or invented number, wrong tool, or a guardrail ignored.

Headline metrics: pass rate (Partial = 0.5), correct-tool rate, correct-signal rate, and
**invented numbers** (any number not backed by a tool result; target 0).

## Failure categories

`wrong-tool`, `wrong-signal`, `wrong-run`, `unit-error`, `calc-error`, `invented-number`,
`no-assumption-stated`, `guardrail-ignored`, `out-of-scope-workaround` (e.g. editing model
files with other tools instead of refusing), `tool-error`, `other`.

## How to run

1. Start from `main` with the latest MBEV run being a standard 1180 s run.
2. Ask each request in a fresh chat (so earlier answers don't help), allow tool calls.
   Connect only `modelica_agent` if possible; otherwise record which other tools (e.g. file
   editing) were available, because the assistant may use them to work around limits.
3. Record the result, tools used, failure category and a short note in a results file:
   `eval/results/<date>-<assistant>.csv`, summarised in `eval/results/<date>-summary.md`.
4. Record the assistant, model and date: answers can change when the model changes.
