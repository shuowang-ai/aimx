# Tasks: Distribution Trace Visual

**Input**: Design documents from `/Users/blizhan/data/code/github/aimx/specs/005-distribution-trace-visual/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-output.md, quickstart.md

**Tests**: Test tasks are included because the feature changes an owned CLI
default, adds a new CLI option, and must preserve existing output contracts,
read-only behavior, safe failure modes, and native Aim passthrough boundaries.

**Organization**: Tasks are grouped by user story so each story can be
implemented and tested as an independently useful increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends
  only on completed foundation work
- **[Story]**: Maps task to a user story (`US1`, `US2`, `US3`)
- Every task includes exact repository-relative file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare distribution-specific test helpers and validation entry
points without changing runtime behavior yet.

- [X] T001 Create reusable multi-step `DistributionSeries` and `DistributionPoint` fixture helpers in `tests/unit/test_trace_distribution_views.py`
- [X] T002 [P] Add distribution integration helpers guarded by repository fixtures in `tests/integration/test_trace_command.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared parser and visual-selection primitives required by the
default visual output and `--step` behavior.

**Critical**: No user story work should begin until this phase is complete.

- [X] T003 [P] Add parser unit tests for accepted `--step`, missing `--step` value, and non-integer `--step` value in `tests/unit/test_trace_helpers.py`
- [X] T004 Extend `TraceInvocation` and `parse_trace_invocation()` with `selected_step: int | None` and `--step N` validation in `src/aimx/commands/trace.py`
- [X] T005 [P] Add unit tests for first non-empty distribution selection, default first point selection, no non-empty series handling, single-step series, and all-zero weights in `tests/unit/test_trace_distribution_views.py`
- [X] T006 Implement distribution visual selection helpers for selected series, selected point, and histogram/heatmap render inputs in `src/aimx/rendering/trace_views.py`
- [X] T007 Run `uv run pytest tests/unit/test_trace_helpers.py tests/unit/test_trace_distribution_views.py -q` and fix foundational failures in `src/aimx/commands/trace.py` and `src/aimx/rendering/trace_views.py`

**Checkpoint**: Parser and visual-selection primitives are ready; user story implementation can start.

---

## Phase 3: User Story 1 - Inspect Distribution Visually By Default (Priority: P1) MVP

**Goal**: Users can run `aimx trace distribution <expression>` without an
output-mode flag and see matched distribution names plus a default histogram
and heatmap for the first selected series.

**Independent Test**: Run `uv run aimx trace distribution "distribution.name != ''" --repo data`
and confirm the output lists all matched names, marks the selected name, labels
the displayed step, shows a current-step histogram, and shows a step-by-bin
heatmap without prompting for interaction (skip manual verification when your
checkout has no histogram data).

### Tests for User Story 1

- [X] T008 [P] [US1] Add renderer unit tests for default visual output sections, selected-name marker, selected context, default first-step label, histogram label, and heatmap label in `tests/unit/test_trace_distribution_views.py`
- [X] T009 [P] [US1] Add integration tests for default `trace distribution "distribution.name != ''" --repo data` visual output in `tests/integration/test_trace_command.py`
- [X] T010 [P] [US1] Add contract tests for default distribution visual output and no-interaction deterministic text output in `tests/contract/test_trace_contract.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `render_distribution_visual()` with `Distributions`, selected step, histogram, and heatmap sections in `src/aimx/rendering/trace_views.py`
- [X] T012 [US1] Route distribution plot/default mode to `render_distribution_visual()` while preserving JSON, CSV, and table branches in `src/aimx/commands/trace.py`
- [X] T013 [US1] Preserve existing no-match and no-data-in-step-range messages for distribution default mode in `src/aimx/commands/trace.py`
- [X] T014 [US1] Run `uv run pytest tests/unit/test_trace_distribution_views.py tests/integration/test_trace_command.py tests/contract/test_trace_contract.py -q` and fix US1 failures in `src/aimx/rendering/trace_views.py` and `src/aimx/commands/trace.py`

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Choose A Display Step Non-Interactively (Priority: P2)

**Goal**: Users can pass `--step N` to choose the current-step histogram in the
default visual output, with deterministic nearest-step fallback.

**Independent Test**: Run `uv run aimx trace distribution "distribution.name != ''" --repo data --step <TRACKED_STEP>`
and confirm `<TRACKED_STEP>` is displayed, then run with a non-tracked step
between two neighbors and confirm the output labels the actual nearest tracked
step.

### Tests for User Story 2

- [X] T015 [P] [US2] Add renderer unit tests for exact step selection, nearest lower step selection, nearest higher step selection, and lower-step tie resolution in `tests/unit/test_trace_distribution_views.py`
- [X] T016 [P] [US2] Add integration tests for dynamic `--step` selection, nearest-step fallback, and labeled actual step output with `--repo data` in `tests/integration/test_trace_command.py`
- [X] T017 [P] [US2] Add contract tests for missing `--step` value and non-integer `--step` exit-code `2` errors in `tests/contract/test_trace_contract.py`

### Implementation for User Story 2

- [X] T018 [US2] Pass `invocation.selected_step` into the default distribution visual renderer from `_render_distribution_trace()` in `src/aimx/commands/trace.py`
- [X] T019 [US2] Implement exact, nearest, and lower-tie selected-step resolution with actual-step labeling in `src/aimx/rendering/trace_views.py`
- [X] T020 [US2] Ensure selected-step request notes are readable with and without ANSI color in `src/aimx/rendering/trace_views.py`
- [X] T021 [US2] Run `uv run pytest tests/unit/test_trace_helpers.py tests/unit/test_trace_distribution_views.py tests/integration/test_trace_command.py tests/contract/test_trace_contract.py -q` and fix US2 failures in `src/aimx/commands/trace.py` and `src/aimx/rendering/trace_views.py`

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Keep Existing Scriptable Outputs (Priority: P3)

**Goal**: Existing `--table`, `--csv`, and `--json` distribution workflows keep
their current tensor/export behavior and do not emit the new default visual
sections.

**Independent Test**: Run distribution trace commands with `--table`, `--csv`,
and `--json` against `data`; confirm each output remains parseable or
readable in its existing shape and excludes the default visual histogram and
heatmap sections.

### Tests for User Story 3

- [X] T022 [P] [US3] Add unit tests proving `render_distribution_table()`, `render_distribution_csv()`, and `render_distribution_json()` keep their existing tensor, CSV, and JSON fields in `tests/unit/test_trace_distribution_views.py`
- [X] T023 [P] [US3] Add integration tests for distribution `--table`, `--csv`, and `--json` against `data`, including `--step` supplied with each explicit mode, in `tests/integration/test_trace_command.py`
- [X] T024 [P] [US3] Add contract tests proving explicit distribution modes exclude default visual sections and remain parseable in `tests/contract/test_trace_contract.py`

### Implementation for User Story 3

- [X] T025 [US3] Ensure `_render_distribution_trace()` branches `--json`, `--csv`, and `--table` before default visual rendering in `src/aimx/commands/trace.py`
- [X] T026 [US3] Preserve `render_distribution_table()`, `render_distribution_csv()`, and `render_distribution_json()` output schemas while adding visual rendering in `src/aimx/rendering/trace_views.py`
- [X] T027 [US3] Ensure `--step` does not filter table, CSV, or JSON rows in explicit distribution modes in `src/aimx/commands/trace.py`
- [X] T028 [US3] Run `uv run pytest tests/unit/test_trace_distribution_views.py tests/integration/test_trace_command.py tests/contract/test_trace_contract.py -q` and fix US3 failures in `src/aimx/commands/trace.py` and `src/aimx/rendering/trace_views.py`

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete discoverability, safety validation, and full regression
coverage across the feature.

- [X] T029 [P] Update trace distribution help text with default visual behavior, `--step`, and explicit `--table` tensor usage in `src/aimx/commands/help.py`
- [X] T030 [P] Update README distribution examples so default output is visual and tensor output uses `--table` in `README.md`
- [X] T031 [P] Update quickstart verification notes if implementation behavior differs from planned examples in `specs/005-distribution-trace-visual/quickstart.md`
- [X] T032 Run quickstart sections 3-9 manually and record any deviations in `specs/005-distribution-trace-visual/quickstart.md`
- [X] T033 Run passthrough and owned-command regression tests with `uv run pytest tests/contract/test_cli_contract.py tests/integration/test_missing_native_aim.py tests/integration/test_missing_python_aim_package.py -q` and fix regressions in `src/aimx/router.py`, `src/aimx/cli.py`, or `src/aimx/commands/trace.py`
- [X] T034 Run the full suite with `uv run pytest -q` and fix any regressions in touched files under `src/aimx/` and `tests/`
- [X] T035 Update final implementation verification notes in `specs/005-distribution-trace-visual/checklists/requirements.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies; can start immediately.
- **Phase 2 Foundational**: Depends on Phase 1; blocks every user story.
- **Phase 3 US1**: Depends on Phase 2; MVP scope.
- **Phase 4 US2**: Depends on Phase 2 and the default visual renderer from US1.
- **Phase 5 US3**: Depends on Phase 2 and can be validated after default visual routing exists.
- **Phase 6 Polish**: Depends on whichever user stories are included in the delivery.

### User Story Dependencies

- **US1 (P1)**: First independently valuable slice; no dependency on US2 or US3.
- **US2 (P2)**: Extends the default visual output with requested-step selection; depends on US1's visual renderer but remains independently testable after US1.
- **US3 (P3)**: Protects structured export behavior; can be worked alongside US1/US2 with coordination around `src/aimx/commands/trace.py`.

### Within Each User Story

- Write tests first and confirm they fail for the missing behavior.
- Parser and selection helpers before renderer routing.
- Renderer behavior before CLI integration assertions.
- Story-specific pytest command before moving to the next priority.

---

## Parallel Opportunities

- T002 can run in parallel with T001 because it touches a different test file.
- T003 and T005 can run in parallel because they touch different behavior areas and no runtime implementation files.
- T008, T009, and T010 can run in parallel for US1 test coverage.
- T015, T016, and T017 can run in parallel for US2 test coverage.
- T022, T023, and T024 can run in parallel for US3 test coverage.
- T029, T030, and T031 can run in parallel during polish because they touch different documentation files.

---

## Parallel Example: User Story 1

```text
Task: "T008 [P] [US1] Add renderer unit tests for default visual output sections, selected-name marker, selected context, default first-step label, histogram label, and heatmap label in tests/unit/test_trace_distribution_views.py"
Task: "T009 [P] [US1] Add integration tests for default `trace distribution \"distribution.name != ''\" --repo data` visual output in tests/integration/test_trace_command.py"
Task: "T010 [P] [US1] Add contract tests for default distribution visual output and no-interaction deterministic text output in tests/contract/test_trace_contract.py"
```

## Parallel Example: User Story 2

```text
Task: "T015 [P] [US2] Add renderer unit tests for exact step selection, nearest lower step selection, nearest higher step selection, and lower-step tie resolution in tests/unit/test_trace_distribution_views.py"
Task: "T016 [P] [US2] Add integration tests for `--step` selection, nearest-step fallback, and labeled actual step output with `--repo data` in tests/integration/test_trace_command.py"
Task: "T017 [P] [US2] Add contract tests for missing `--step` value and non-integer `--step` exit-code `2` errors in tests/contract/test_trace_contract.py"
```

## Parallel Example: User Story 3

```text
Task: "T022 [P] [US3] Add unit tests proving `render_distribution_table()`, `render_distribution_csv()`, and `render_distribution_json()` keep their existing tensor, CSV, and JSON fields in tests/unit/test_trace_distribution_views.py"
Task: "T023 [P] [US3] Add integration tests for distribution `--table`, `--csv`, and `--json` against `data`, including `--step` supplied with each explicit mode, in tests/integration/test_trace_command.py"
Task: "T024 [P] [US3] Add contract tests proving explicit distribution modes exclude default visual sections and remain parseable in tests/contract/test_trace_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational parser and visual-selection helpers.
3. Complete Phase 3 US1.
4. Stop and validate `uv run aimx trace distribution "distribution.name != ''" --repo data`.
5. Run US1 unit, integration, and contract tests before adding `--step` behavior.

### Incremental Delivery

1. US1: deliver default distribution name list, selected histogram, and heatmap.
2. US2: add `--step` exact and nearest-step visual selection.
3. US3: protect explicit table, CSV, and JSON export behavior.
4. Polish: update docs, run quickstart, and run full regression suite.

### Multi-Developer Coordination

- One developer owns `src/aimx/commands/trace.py` during parser and routing tasks to avoid conflicts.
- One developer can own `src/aimx/rendering/trace_views.py` and `tests/unit/test_trace_distribution_views.py`.
- One developer can own integration and contract tests in `tests/integration/test_trace_command.py` and `tests/contract/test_trace_contract.py`.
- Documentation tasks can proceed after the CLI shape is stable.

---

## Notes

- `[P]` means the task can be parallelized only after its stated phase dependencies are satisfied.
- Story labels map directly to the spec user stories.
- Keep the command read-only; do not call Aim mutation APIs such as `run.set`, `track`, artifact logging, migration, or repair operations.
- Preserve existing metric trace, distribution table, distribution CSV, distribution JSON, and native Aim passthrough contracts throughout implementation.
- Commit after each phase or a small coherent task group when using the git hook workflow.
