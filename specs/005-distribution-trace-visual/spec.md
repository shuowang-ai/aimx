# Feature Specification: Distribution Trace Visual

**Feature Branch**: `005-distribution-trace-visual`  
**Created**: 2026-04-30  
**Status**: Draft  
**Input**: User description: "Modify the current distribution trace command so the default experience more closely matches the Aim web Distributions tab: show which distribution names are available, default to a visual non-interactive output similar to trace metrics, include a current-step histogram and a step-by-bin heatmap, support a step selection option, and preserve existing `--table`, `--csv`, and `--json` outputs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Distribution Visually By Default (Priority: P1)

An Aim user runs the distribution trace command against a local repository and immediately sees a readable visual summary instead of a tensor table. The output shows the matched distribution names and visualizes the first matched distribution in a way that resembles the Aim web Distributions tab.

**Why this priority**: This is the core requested workflow and closes the gap between the current terminal output and the web UI.

**Independent Test**: Run the distribution trace command against a repository with multiple distribution series and no explicit output mode; verify that the command exits successfully, lists matched distribution names, marks the first match as selected, and renders both a current-step histogram and a cross-step heatmap for that selected series.

**Acceptance Scenarios**:

1. **Given** a local Aim repository containing multiple distributions, **When** the user runs `aimx trace distribution <expression>` without an output-mode flag, **Then** the output lists the matched distribution names and visually renders only the first matched series.
2. **Given** the selected distribution has data from step 300 through later steps, **When** the user runs the default distribution trace command, **Then** the current-step histogram uses the first available step and labels the actual step displayed.
3. **Given** the selected distribution has values across multiple steps, **When** the user runs the default distribution trace command, **Then** the output includes a step-by-bin heatmap that communicates how the distribution changes over the available steps.

---

### User Story 2 - Choose A Display Step Non-Interactively (Priority: P2)

An Aim user wants to inspect a specific training step from the terminal without opening the web UI or entering an interactive selector.

**Why this priority**: Step selection makes the visual output useful for targeted debugging while preserving a single-command, script-friendly workflow.

**Independent Test**: Run the distribution trace command with a requested step that exists and with one that does not exist; verify that the visual output displays the exact step when available and the nearest tracked step otherwise.

**Acceptance Scenarios**:

1. **Given** a selected distribution with a tracked step of 12300, **When** the user runs `aimx trace distribution <expression> --step 12300`, **Then** the current-step histogram displays step 12300.
2. **Given** a selected distribution without a tracked step of 1000, **When** the user runs `aimx trace distribution <expression> --step 1000`, **Then** the current-step histogram displays the nearest tracked step and labels the actual step used.
3. **Given** two tracked steps are equally close to the requested step, **When** the user runs the command with that requested step, **Then** the earlier tracked step is selected and labeled.

---

### User Story 3 - Keep Existing Scriptable Outputs (Priority: P3)

An Aim user or automation already depends on distribution tensor output in table, CSV, or JSON form and should not lose those workflows when the default output changes.

**Why this priority**: `aimx` is CLI-first and scriptable; visual defaults must not break existing export and diagnostic usage.

**Independent Test**: Run distribution trace commands with `--table`, `--csv`, and `--json`; verify that each mode remains available, keeps the same data shape as before, and does not emit the new default visual summary.

**Acceptance Scenarios**:

1. **Given** a distribution query with matching data, **When** the user runs the command with `--table`, **Then** the output remains a tensor table with step, epoch, and tensor content.
2. **Given** a distribution query with matching data, **When** the user runs the command with `--csv`, **Then** the output remains parseable CSV with distribution histogram fields.
3. **Given** a distribution query with matching data, **When** the user runs the command with `--json`, **Then** the output remains parseable JSON with each distribution's points, bin edges, and weights.

### Edge Cases

- If the expression matches no distributions, the command exits successfully and reports that no matching distributions were found.
- If step filtering or sampling removes all points from every matched series, the command exits successfully and reports that no data remains in the requested step range.
- If a matched distribution has a name and context but no points, it is listed only when relevant to the mode and is not selected for visual rendering unless no non-empty series exist.
- If the selected distribution contains a single tracked step, the histogram is still shown and the heatmap degrades to a single-step view.
- If the selected distribution has empty or all-zero histogram weights at the selected step, the histogram and heatmap still render with clear labels rather than failing.
- If terminal output is captured in a non-interactive environment, the default visual output remains deterministic text output and does not require keyboard or mouse interaction.
- If `--step` is provided with a non-default output mode, the export modes keep their existing full-data behavior; the step selection only affects the default visual view.

## Constitution Alignment *(mandatory)*

- **CA-001 Safety & Mutability**: This feature is read-only. It inspects distribution data from existing Aim repositories and must not modify the installed Aim package or mutate `.aim` repository data.
- **CA-002 Ownership Boundary**: `aimx` owns the existing `aimx trace distribution` command path and the new default visual behavior for that path. Native Aim passthrough remains unchanged for all unowned command paths.
- **CA-003 CLI & Output Contract**: The command remains usable in local shells, SSH sessions, captured logs, and CI. It provides a human-readable default visual output and preserves existing machine-readable `--csv` and `--json` outputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The default `aimx trace distribution <expression>` output MUST list all matched distribution names before rendering the selected distribution.
- **FR-002**: The default output MUST identify which matched distribution is selected for visual rendering.
- **FR-003**: When multiple distributions match, the default output MUST select the first matched distribution for visual rendering.
- **FR-004**: The default visual output MUST include a histogram for one selected step of the selected distribution.
- **FR-005**: The default selected step MUST be the first available step after expression matching, step filtering, and sampling are applied.
- **FR-006**: Users MUST be able to request a selected visual step with `--step N` in default visual mode.
- **FR-007**: If the requested visual step is not tracked, the command MUST use the nearest tracked step and label the actual step displayed.
- **FR-008**: The default visual output MUST include a step-by-bin heatmap for the selected distribution across the available displayed steps.
- **FR-008a**: When color is enabled, the default visual output MUST use a Rich-rendered blue gradient inspired by the Aim web Distributions tab rather than the metric plot's high-contrast terminal palette.
- **FR-009**: The default visual output MUST remain non-interactive and MUST complete from a single command invocation.
- **FR-010**: The existing `--table` output mode MUST remain available and keep the existing tensor-table workflow.
- **FR-011**: The existing `--csv` output mode MUST remain available and keep parseable distribution histogram export data.
- **FR-012**: The existing `--json` output mode MUST remain available and keep parseable distribution histogram export data.
- **FR-013**: Existing filtering and sampling options, including step ranges and head, tail, or interval sampling, MUST continue to apply before default visual rendering.
- **FR-014**: Existing display controls such as width, height, and no-color behavior MUST remain accepted where they are already part of the trace command surface.
- **FR-015**: Error and empty-result messages MUST remain concise, non-destructive, and free of traceback-style output for expected user-facing conditions.

### Key Entities

- **Distribution Match**: A distribution series returned by the user's expression, including run identity, name, context, and tracked points.
- **Distribution Name List**: The ordered set of matched distribution names shown to the user so they can see what the expression found.
- **Distribution Point**: A tracked step and optional epoch with histogram bin edges and weights.
- **Selected Distribution**: The first non-empty distribution series chosen for default visual rendering.
- **Selected Step**: The tracked step used for the current-step histogram, either the default first step or the nearest tracked step to the user's requested value.
- **Visual Distribution Output**: The non-interactive default output containing the name list, current-step histogram, and step-by-bin heatmap.
- **Structured Export Output**: The table, CSV, or JSON output selected by explicit output-mode flags.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can run a default distribution trace command against a repository with at least 16 matched distributions and identify the available names and selected visualized name in one command result.
- **SC-002**: For a selected distribution with at least 40 tracked steps and 64 histogram bins, the default command result shows both a current-step histogram and a cross-step heatmap without requiring follow-up interaction.
- **SC-003**: A requested visual step that does not exactly exist resolves to a labeled tracked step in 100% of valid default visual runs.
- **SC-004**: Existing `--table`, `--csv`, and `--json` distribution commands continue to produce parseable output with zero intentional schema changes.
- **SC-005**: Expected empty-result and invalid-step-range conditions complete without repository mutation and without traceback-style output.

## Assumptions

- Users already know how to narrow distribution results with the existing expression syntax when they want a distribution other than the first match.
- The first matched distribution is an acceptable default selection because it mirrors the web UI's default expanded item behavior.
- The default visual output is intended as a static terminal snapshot, not as an interactive terminal UI.
- Step selection affects only the default visual view; structured exports remain full-data outputs controlled by expression, filtering, and sampling options.
- Developers may validate multi-name distribution visuals against any local Aim repository that contains matching distribution sequences (for example the repository rooted at `data/` described in contributor docs); CI keeps reliability via deterministic unit fixtures while integration coverage skips when no distributions exist.
