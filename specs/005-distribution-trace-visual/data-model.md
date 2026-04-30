# Phase 1 Data Model: Distribution Trace Visual

**Feature**: `005-distribution-trace-visual`

## Trace Distribution Invocation

Represents one CLI request to inspect distribution traces.

**Fields**:

- `target`: literal `distribution`
- `expression`: Aim distribution query expression supplied by the user
- `repo_path`: local repository root or `.aim` path
- `mode`: one of default visual, table, CSV, or JSON
- `step_slice`: optional inclusive step range filter
- `selected_step`: optional visual step requested with `--step N`
- `head`, `tail`, `every`: optional sampling controls
- `width`, `height`: optional display controls for visual output
- `no_color`: boolean terminal styling control

**Validation Rules**:

- `expression` must be present for distribution traces.
- `repo_path` must exist and is normalized consistently with existing trace
  commands.
- `--step` requires an integer value.
- Sampling and filtering controls are applied before visual selection.
- `selected_step` affects only default visual output; structured export modes
  preserve their existing full-series behavior.

## Distribution Match

Represents one distribution series returned by the user's expression.

**Fields**:

- `run`: run identity with hash, experiment, optional name, and optional
  creation time
- `name`: distribution name
- `context`: distribution context key-value mapping
- `points`: ordered list of distribution points

**Relationships**:

- One Trace Distribution Invocation produces zero or more Distribution Matches.
- One Distribution Match contains zero or more Distribution Points.
- Distribution Matches form the Distribution Name List in the default visual
  output.

**Validation Rules**:

- Match order is preserved from the collection pipeline so default selection is
  deterministic.
- Empty `points` are allowed but are skipped for selected visual rendering when
  a later non-empty match exists.
- Context values are displayed compactly in human-readable output and remain
  preserved in structured output.

## Distribution Point

Represents one tracked histogram at one step.

**Fields**:

- `step`: tracked training step
- `epoch`: optional epoch value
- `bin_edges`: ordered numeric bin edges
- `weights`: ordered numeric histogram weights

**Relationships**:

- Belongs to one Distribution Match.
- One selected Distribution Point powers the current-step histogram.
- All displayed points in the selected series power the step-by-bin heatmap.

**Validation Rules**:

- `weights` may be all zeros.
- `bin_edges` and `weights` must be paired so the histogram can label bins
  coherently.
- Single-point series are valid and produce a single-step heatmap.

## Distribution Name List

The ordered human-readable list of matched distribution names shown before the
default visual charts.

**Fields**:

- `items`: ordered names and compact context labels
- `selected_index`: index of the distribution selected for visual rendering
- `selected_label`: selected distribution display label

**Relationships**:

- Built from Distribution Matches.
- References the Selected Distribution by index and label.

**Validation Rules**:

- All matched distribution names are listed.
- The selected item is visibly marked.
- Duplicate names remain distinguishable by context or run label when present.

## Selected Distribution

The distribution series rendered by default visual mode.

**Fields**:

- `series`: selected Distribution Match
- `selected_point`: resolved Distribution Point for the current-step histogram
- `requested_step`: optional step requested by the user
- `resolved_step`: actual tracked step displayed
- `step_resolution`: exact, nearest-lower, nearest-higher, or default-first

**Relationships**:

- Derived from the Distribution Name List and available Distribution Points.
- Supplies data to Histogram View and Heatmap View.

**Validation Rules**:

- If `requested_step` exactly matches a point, select that point.
- If `requested_step` does not match, select the point with minimum absolute
  distance to the requested value.
- If two points are equally close, select the lower step.
- If no non-empty distribution exists after filtering and sampling, visual
  rendering is skipped and the command reports no data.

## Histogram View

The current-step chart for the selected distribution.

**Fields**:

- `title`: selected distribution name and resolved step
- `x_values`: bin centers or labels derived from bin edges
- `weights`: histogram weights for the selected point
- `step_label`: actual tracked step displayed
- `request_note`: optional note when nearest-step fallback was used

**Validation Rules**:

- Must render even when all weights are zero.
- Must label the actual displayed step.
- Must remain deterministic when terminal color is disabled.

## Heatmap View

The cross-step chart for the selected distribution.

**Fields**:

- `step_values`: ordered tracked steps after filtering and sampling
- `bin_values`: bin labels or centers
- `weight_matrix`: rows or columns of histogram weights aligned with steps and
  bins
- `color_scale_label`: textual scale or legend for weight intensity

**Validation Rules**:

- Must include every displayed point in the selected distribution.
- Must degrade to a single-step heatmap for single-point series.
- Must not mutate or normalize stored histogram data in the repository.

## Structured Export Output

The explicit table, CSV, or JSON output selected by mode flags.

**Fields**:

- Existing distribution table fields: step, epoch, tensor summary
- Existing CSV fields: run hash, experiment, distribution, context, step,
  epoch, bin edges, weights
- Existing JSON fields: run, distribution, context, count, points with bin
  edges and weights

**Validation Rules**:

- Explicit structured modes do not include the new default visual name list,
  histogram, or heatmap.
- CSV and JSON remain parseable with the existing field names.
- Table mode remains a tensor inspection view.
