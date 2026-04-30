# Implementation Plan: Distribution Trace Visual

**Branch**: `005-distribution-trace-visual` | **Date**: 2026-04-30 | **Spec**: [spec.md](/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/spec.md)
**Input**: Feature specification from `/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/spec.md`

## Summary

Change the owned `aimx trace distribution` default mode from a tensor table to
a non-interactive terminal visual summary that mirrors the Aim web
Distributions tab: list all matched distribution names, mark the first
non-empty match as selected, render a current-step histogram, and render a
step-by-bin heatmap for that selected series. Add `--step N` for visual step
selection using nearest tracked-step fallback. Preserve existing `--table`,
`--csv`, and `--json` distribution outputs without intentional schema changes.
The implementation stays read-only, uses existing trace command/data/rendering
boundaries, and introduces no new runtime dependency.

## Technical Context

**Language/Version**: Python 3.12 for development, runtime support `>=3.10,<3.13`  
**Primary Dependencies**: Python standard library, `numpy>=1.24`, `rich>=13.7`, `plotext>=5.3`, existing Aim SDK usage for owned trace commands; no new runtime dependency planned  
**Storage**: Existing local Aim repositories on disk, read-only; distribution histogram points are read from Aim sequence data under `.aim`  
**Testing**: pytest unit, integration, and contract suites; integration and contract coverage exercises real Aim distribution queries against `tests/conftest.py`'s `sample_repo_root` (`Path("data")`) when matching sequences exist and skips cleanly otherwise so CI stays green without extra fixtures  
**Target Platform**: Terminal-first CLI for local shells, SSH sessions, scripts, and CI on Python-supported platforms  
**Project Type**: Single-project Python CLI application  
**Performance Goals**: Default visual rendering stays bounded to one command invocation for realistic repositories with multiple matched distributions and many tracked histogram steps (such as training runs logged from TensorBoard imports), remaining readable on a standard terminal width  
**Constraints**: Read-only; preserve native Aim passthrough behavior; preserve existing distribution `--table`, `--csv`, and `--json` output contracts; keep default output non-interactive; avoid adding GUI or TUI dependencies  
**Scale/Scope**: One owned command path (`trace distribution`), one visual-only option (`--step N`), default distribution visual renderer, help/README updates, and focused unit/integration/contract tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Safe coexistence: default distribution visual rendering only reads local
      Aim distribution sequence data; no normal-path change modifies the
      installed `aim` package, replaces the native `aim` executable, or mutates
      `.aim` repo data.
- [x] Ownership boundary: `aimx` already owns `aimx trace distribution`; the
      plan adds owned default rendering behavior and the owned `--step` option
      for that command path only. Native `aim` passthrough remains unchanged.
- [x] Read-only default: all behavior is inspection-only and uses no Aim
      mutation APIs.
- [x] CLI-first contract: the default output is deterministic non-interactive
      terminal text, while existing `--table`, `--csv`, and `--json` modes
      remain available for diagnostics and automation.
- [x] Compatibility plan: design reuses current distribution collection,
      filtering, sampling, repo normalization, and trace error handling; tests
      cover default visual output plus non-regression for existing modes.

## Project Structure

### Documentation (this feature)

```text
/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-output.md
├── checklists/
│   └── requirements.md
└── tasks.md            # created later by /speckit.tasks
```

### Source Code (repository root)

```text
/Users/blizhan/data/code/github/aimx/
├── README.md
├── src/aimx/
│   ├── commands/
│   │   ├── help.py                    # update trace distribution usage text
│   │   └── trace.py                   # parse --step and route default distribution mode
│   ├── aim_bridge/
│   │   └── metric_stats.py            # keep DistributionSeries/Point filtering and sampling helpers
│   └── rendering/
│       └── trace_views.py             # add default distribution visual renderer
└── tests/
    ├── contract/
    │   └── test_trace_contract.py     # add distribution output contract coverage
    ├── integration/
    │   └── test_trace_command.py      # add distribution CLI coverage guarded by repo fixtures
    └── unit/
        ├── test_trace_distribution_views.py
        └── test_trace_helpers.py
```

**Structure Decision**: Keep the existing single-project CLI layout. The trace
command remains the orchestration boundary for parsing, repo normalization,
filtering, sampling, and mode selection. The Aim bridge keeps returning
`DistributionSeries` records. The visual work belongs in
`rendering/trace_views.py` next to existing metric plots and distribution
table/CSV/JSON renderers.

## Phase 0: Research Summary

Phase 0 decisions are captured in [research.md](/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/research.md). Key outcomes:

- Keep `aimx trace distribution` as the user-facing command and change only its
  default mode; no TUI, no new top-level command, and no new selector command.
- Reuse existing `DistributionSeries` / `DistributionPoint` data and filtering
  behavior, selecting the first non-empty series after expression matching,
  step filtering, and sampling.
- Add `--step N` as a visual-only selector. Exact matches are used directly;
  otherwise the nearest tracked step is selected, with lower step winning ties.
- Reuse existing plotting/rendering dependencies. `plotext` is available for
  histogram and heatmap-style terminal output, while `rich` can frame labels
  and the matched-name list consistently with existing views.
- Preserve `--table`, `--csv`, and `--json` as non-visual modes with unchanged
  data shapes.

## Phase 1: Design Summary

- Extend `TraceInvocation` with `selected_step: int | None` and parse `--step N`
  in `parse_trace_invocation`. Reject missing or non-integer values with exit
  code `2` through the existing error path.
- Treat `--step` as relevant to default distribution visual mode. `--table`,
  `--csv`, and `--json` keep their current full-series behavior even when
  `--step` is supplied.
- Add a distribution visual render path in `_render_distribution_trace`: JSON
  and CSV keep current renderers, table keeps the current tensor-table renderer,
  and default plot mode calls a new visual renderer.
- Implement a visual selection helper that receives filtered/sampled
  `DistributionSeries` records, builds the ordered name list, selects the first
  non-empty series, resolves the selected step, and returns a render model for
  histogram and heatmap output.
- Implement the default visual renderer with three sections:
  - `Distributions`: ordered matched names with a selected marker and compact
    context for the selected item.
  - `Histogram`: selected distribution name, selected step label, and
    Rich-rendered blue-gradient bin-weight histogram for the resolved step.
  - `Heatmap`: step-by-bin view for the selected distribution across available
    displayed points, using the same web-style blue intensity scale.
- Keep no-match and no-data messages on the existing successful, non-throwing
  path. Add specific tests for empty points, single-step series, all-zero
  weights, and nearest-step tie behavior.
- Update README/help text so default distribution output is documented as
  visual, while tensor-table usage moves behind explicit `--table`.

## Post-Design Constitution Check

- [x] Safe coexistence: design reads distribution query results and histogram
      arrays only; no installed Aim package, executable, or repository data is
      modified.
- [x] Ownership boundary: all new behavior is contained inside the existing
      `aimx trace distribution` command path and its documented options.
- [x] Read-only default: visual selection, plotting, and export rendering are
      derived from in-memory query results.
- [x] CLI-first contract: [contracts/cli-output.md](/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/contracts/cli-output.md)
      defines default visual output, structured modes, exit statuses, and
      non-regression expectations.
- [x] Compatibility: existing trace command tests remain part of validation;
      new integration tests query real Aim repositories when distributions exist
      and assert no schema change for table, CSV, or JSON modes.

## Complexity Tracking

No constitution violations; no exceptional complexity requires justification.
The feature uses existing project boundaries and dependencies.
