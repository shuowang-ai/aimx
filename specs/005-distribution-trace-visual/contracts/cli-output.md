# CLI Output Contract: `aimx trace distribution`

**Feature**: `005-distribution-trace-visual`

This contract defines the observable CLI behavior for distribution trace
visualization and exports.

## Command Shape

```text
aimx trace distribution <expression> [--repo <path>]
                              [--steps start:end]
                              [--head N] [--tail N] [--every K]
                              [--step N]
                              [--width W] [--height H] [--no-color]
                              [--table | --csv | --json]
```

## Owned Options

| Option | Applies To | Behavior |
|--------|------------|----------|
| `--repo <path>` | all modes | Uses a local Aim repository root or `.aim` directory. Defaults to the current directory. |
| `--steps start:end` | all modes | Filters distribution points by inclusive tracked step range before sampling and rendering. |
| `--head N` | all modes | Keeps the first `N` points per matched series before rendering or export. |
| `--tail N` | all modes | Keeps the last `N` points per matched series before rendering or export. |
| `--every K` | all modes | Keeps every `K`th point per matched series before rendering or export. |
| `--step N` | default visual mode | Chooses the current-step histogram step; nearest tracked step is used when no exact match exists. |
| `--width W` | default visual mode | Sets preferred chart width when supported by the renderer. |
| `--height H` | default visual mode | Sets preferred chart height when supported by the renderer. |
| `--no-color` | human-readable modes | Disables ANSI styling where applicable. |
| `--table` | explicit table mode | Emits the existing tensor table and no default visual charts. |
| `--csv` | explicit CSV mode | Emits existing CSV histogram rows and no default visual charts. |
| `--json` | explicit JSON mode | Emits existing JSON series payload and no default visual charts. |

## Query Expression

The expression is passed to Aim's distribution-query evaluator after existing
short `run.hash` expansion and the documented singular `distribution` alias
normalization.

Examples:

```bash
aimx trace distribution "distribution.name != ''" --repo data
aimx trace distribution "distribution.name == '<name-from-your-repo>'" --repo data --step <tracked-step>
aimx trace distribution "distribution.context.kind == 'weights'" --repo data --json
```

Replace `<name-from-your-repo>` and `<tracked-step>` with values present in your Aim repository; the commands illustrate syntax only.

## Default Visual Output

Default output is non-interactive terminal text. It contains these sections in
order:

1. Distribution name list
2. Selected distribution context and current-step label
3. Current-step histogram
4. Step-by-bin heatmap

The distribution name list must show every matched distribution name in
collection order. The selected item must be visibly marked. When more than one
series matches, only the selected series is visualized.

The selected series is the first non-empty matched series after filtering and
sampling. The default selected step is the first available point in that
series. When `--step N` is provided:

- if `N` is tracked, display `N`
- if `N` is not tracked, display the nearest tracked step
- if two steps are equally close, display the lower step
- always label the actual displayed step

## Table Output

`--table` keeps the existing distribution tensor table workflow:

```text
<run> · <experiment> · <distribution> · <context>   <count> points
 STEP  EPOCH  TENSOR
  300      0  [1, 1, 0, 1, ...] (64 bins)
```

This mode must not include the default distribution name list, histogram, or
heatmap.

## CSV Output

`--csv` remains parseable CSV with the existing field names:

```text
run_hash,experiment,distribution,context,step,epoch,bin_edges,weights
```

Each data row represents one distribution point. `bin_edges` and `weights`
remain JSON-encoded arrays inside CSV cells.

## JSON Output

`--json` remains parseable JSON with the existing top-level shape: a list of
distribution series.

Each series contains:

- `run`
- `distribution`
- `context`
- `count`
- `points`

Each point contains:

- `step`
- `epoch`
- `bin_edges`
- `weights`

## Exit Status

| Condition | Exit Status | Output |
|-----------|-------------|--------|
| Valid default visual query with one or more non-empty matches | `0` | Distribution list, selected histogram, heatmap |
| Valid table, CSV, or JSON query with matches | `0` | Explicit mode output |
| Valid query with zero matches | `0` | Explicit no-matches message or empty structured output if already defined by that mode |
| Filtering removes all data | `0` | Explicit no-data-in-range message |
| Requested visual step is absent but another point exists | `0` | Nearest tracked step rendered and labeled |
| Missing repository path | `2` | Actionable error on stderr |
| Invalid query expression | `2` | Actionable error on stderr |
| Missing or non-integer `--step` value | `2` | Actionable error on stderr |
| Invalid sampling or step-range option | `2` | Actionable error on stderr |

## Non-Regression Requirements

- Metric trace default plot, table, CSV, and JSON outputs remain unchanged.
- Distribution `--table`, `--csv`, and `--json` outputs keep existing field
  names and parseability.
- Existing `--steps`, `--head`, `--tail`, `--every`, `--width`, `--height`, and
  `--no-color` parsing behavior remains compatible except for the documented
  addition of `--step`.
- Commands outside owned `aimx` surfaces continue to delegate to native `aim`.
