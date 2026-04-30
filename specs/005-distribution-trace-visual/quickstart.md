# Quickstart: Distribution Trace Visual

**Feature**: `005-distribution-trace-visual`

## 1. Prepare The Environment

```bash
uv sync
```

Point `--repo` at an Aim repository root that contains `.aim` metadata. This
guide uses the contributor-local checkout rooted at `data/` (see `AGENTS.md`):

```text
/Users/blizhan/data/code/github/aimx/data/.aim
```

If your checkout does not contain distribution histogram sequences yet, most
CLI sections below still validate `--table`, `--csv`, `--json`, and no-match
behavior; default visualization sections require at least one matched
distribution series.

## 2. Inspect Available Steps (Optional)

Pick a tracked step value from your repository before trying `--step`:

```bash
uv run aimx trace distribution "distribution.name != ''" \
  --repo data --json --head 1 | python - <<'PY'
import json, sys
payload = json.load(sys.stdin)
if not payload:
    raise SystemExit("No distribution series matched this repository.")
steps = sorted({point["step"] for series in payload for point in series["points"]})
print("sample steps:", steps[:5], "... total", len(steps))
PY
```

Use any printed step as `<TRACKED_STEP>` below.

## 3. Render The Default Distribution Visual

```bash
uv run aimx trace distribution "distribution.name != ''" --repo data
```

Expected result:

- exit code `0` when distributions exist (otherwise Aim reports no matches)
- output includes a `Distributions` name list when matches exist
- the first matched distribution is marked as selected
- output labels the current displayed step
- output includes a current-step histogram
- output includes a step-by-bin heatmap
- command does not prompt for keyboard or mouse input

## 4. Select A Specific Step

```bash
uv run aimx trace distribution "distribution.name != ''" \
  --repo data --step <TRACKED_STEP>
```

Expected result:

- exit code `0`
- current-step histogram labels step `<TRACKED_STEP>`
- heatmap still covers the displayed points for the selected series

## 5. Select A Nearest Step

Pick two consecutive tracked steps `LOWER` and `HIGHER` from section 2, choose a
non-tracked integer `REQUESTED` strictly between them, then run:

```bash
uv run aimx trace distribution "distribution.name != ''" \
  --repo data --step <REQUESTED>
```

Expected result:

- exit code `0`
- output labels the actual tracked step chosen (nearest tracked step, lower
  step wins on ties)
- no traceback is printed

## 6. Keep Tensor Table Output

```bash
uv run aimx trace distribution "distribution.name != ''" --repo data --table --head 2
```

Expected result:

- exit code `0`
- output contains `STEP`, `EPOCH`, and `TENSOR`
- output does not include the default visual histogram or heatmap sections

## 7. Keep JSON Output

```bash
uv run aimx trace distribution "distribution.name != ''" --repo data --json --head 1
```

Expected result:

- valid JSON
- top-level value is a list
- each series contains `run`, `distribution`, `context`, `count`, and `points`
- each point contains `step`, `epoch`, `bin_edges`, and `weights`

## 8. Keep CSV Output

```bash
uv run aimx trace distribution "distribution.name != ''" --repo data --csv --head 1
```

Expected result:

- valid CSV
- header includes `run_hash`, `experiment`, `distribution`, `context`,
  `step`, `epoch`, `bin_edges`, and `weights`

## 9. No-Match Behavior

```bash
uv run aimx trace distribution "distribution.name == 'missing-distribution'" --repo data
```

Expected result:

- exit code `0`
- output reports no matching distributions
- no traceback is printed

## 10. Test Commands

```bash
uv run pytest tests/unit/test_trace_helpers.py tests/unit/test_trace_distribution_views.py -q
uv run pytest tests/integration/test_trace_command.py -q
uv run pytest tests/contract/test_trace_contract.py -q
uv run pytest -q
```

## Verification Notes

- Automated integration and contract suites skip distribution scenarios when the
  configured `sample_repo_root` repository has no histogram data, which keeps CI
  green without checking in custom fixtures.
- When your local `data/` repository contains distributions, the commands above
  provide the same observability checks that previously relied on ad hoc test
  directories.
- `uv run` may emit an environment warning about a missing
  `aimx-*.dist-info/RECORD` during editable reinstall; commands and tests should
  still complete successfully.
