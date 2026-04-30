# Phase 0 Research: Distribution Trace Visual

**Feature**: `005-distribution-trace-visual`  
**Date**: 2026-04-30

## Decision: Keep The Existing `trace distribution` Command

Use `aimx trace distribution <expression>` as the command surface and change
only the default mode for distribution traces.

**Rationale**: The project already owns the trace distribution command path,
and users already query distributions through Aim-style expressions there.
Changing the default mode keeps the feature discoverable and aligns with the
existing `aimx trace <metric-expression>` behavior, where the unflagged command
is visual and explicit flags select table or structured output.

**Alternatives considered**:

- Add a new top-level distribution command: rejected because it duplicates the
  existing owned trace surface and fragments query/filtering behavior.
- Add an interactive terminal UI: rejected because the requested behavior is
  non-interactive and the constitution prioritizes predictable CLI workflows.
- Add a separate name selector command: rejected for v1 because the matched
  name list already gives users the expression targets they need.

## Decision: Select The First Non-Empty Matched Series By Default

Default visual mode lists all matched distribution names but renders only the
first non-empty series after expression matching, step filtering, and sampling.

**Rationale**: This mirrors the Aim web page's default expanded item while
preventing large terminal output when an expression matches many names. The
list of matched names preserves discoverability and tells users how to narrow
their expression when they want another series.

**Alternatives considered**:

- Render every matched distribution: rejected because terminal output becomes
  noisy when an expression matches many series (for example repositories that
  import wide TensorBoard histogram tiles).
- Refuse to render until the user narrows to one name: rejected because it
  makes the default command less useful than the web page.
- Select the last matched distribution: rejected because it is less consistent
  with the web UI's first expanded item.

## Decision: Add `--step N` For Visual Step Selection

Add `--step N` so users can choose the current-step histogram in default visual
mode. Exact tracked steps are used directly. If the requested step is not
tracked, the nearest tracked step is used and the actual displayed step is
labeled. If two tracked steps are equally near, choose the earlier step.

**Rationale**: The default step should match the web page's first step, but
terminal users often need to inspect a later training step without opening the
web UI. Nearest-step fallback keeps the command forgiving while still being
deterministic.

**Alternatives considered**:

- Always use the first tracked step: rejected because it prevents targeted
  debugging from the CLI.
- Always use the last tracked step: rejected because it diverges from the web
  page's default behavior that motivated the request.
- Require exact step matches only: rejected because users may not know the
  repository's tracked step interval.

## Decision: Keep `--step` Visual-Only

`--step` affects only default visual rendering. `--table`, `--csv`, and
`--json` continue to emit the filtered/sampled distribution series according
to their existing contracts.

**Rationale**: Existing table/CSV/JSON behavior is useful precisely because it
exports all available points after filtering and sampling. Applying `--step` to
those modes would be an intentional schema or row-count behavior change and
could surprise scripts.

**Alternatives considered**:

- Filter all output modes to the selected step: rejected because it changes
  existing export semantics.
- Reject `--step` with non-default modes: rejected because the option can be
  harmlessly ignored for compatibility and keeps parser behavior simple.

## Decision: Reuse Existing Terminal Rendering Dependencies

Use the current rendering dependencies for default visual output: `plotext` for
histogram/heatmap-style charts and `rich` for labels, list formatting, and
no-color behavior.

**Rationale**: `plotext` is already used by metric trace plots and provides
histogram, bar, and heatmap/matrix plotting helpers in the local environment.
`rich` is already used for trace tables and query views. Reusing both avoids a
new dependency and keeps output behavior consistent with the rest of `aimx`.

**Alternatives considered**:

- Add a dedicated TUI or plotting dependency: rejected because it increases
  dependency surface for a static terminal snapshot.
- Hand-roll all plotting with ad hoc string output: rejected because existing
  terminal plotting support is already available and tested in trace metrics.
- Generate image files: rejected because the feature should work in shell, SSH,
  and CI-style output without file management.

## Decision: Prefer Local Repositories Like `data/` For Integration Coverage

Exercise real Aim distribution queries against whatever repository contributors
already mount at `tests/conftest.py`'s `sample_repo_root` (`Path("data")`),
typically `/Users/blizhan/data/code/github/aimx/data/.aim`.

**Rationale**: Keeping validation anchored on `data/` matches contributor docs,
avoids committing bespoke `.aim` fixtures, and still walks the Aim SDK query path.
pytest skips integration and contract assertions when no distributions exist so
remote CI stays deterministic without shipping histogram data.

**Alternatives considered**:

- Require every checkout to ship a curated `.aim` fixture: rejected because it
  bloats the repository and duplicates what operators already store locally.
- Rely only on unit fixtures: partially adopted for determinism, but paired with
  optional integration coverage whenever local distributions exist.
