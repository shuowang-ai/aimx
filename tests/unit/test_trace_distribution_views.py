from __future__ import annotations

import csv
import io
import json

import numpy as np

from aimx.aim_bridge.metric_stats import DistributionPoint, DistributionSeries, RunMeta
from aimx.rendering.trace_views import (
    render_distribution_csv,
    render_distribution_json,
    render_distribution_table,
    render_distribution_visual,
    select_distribution_visual,
)


def _sample_distribution_series() -> list[DistributionSeries]:
    run = RunMeta(hash="1234567890abcdef", experiment="exp-a", name=None, creation_time=None)
    return [
        DistributionSeries(
            run=run,
            name="weights",
            context={"subset": "train"},
            points=[
                DistributionPoint(
                    step=10,
                    epoch=1.0,
                    bin_edges=np.array([0.0, 1.0, 2.0]),
                    weights=np.array([3.0, 5.0]),
                ),
                DistributionPoint(
                    step=20,
                    epoch=2.0,
                    bin_edges=np.array([0.0, 1.0, 2.0]),
                    weights=np.array([2.0, 4.0]),
                ),
            ],
        )
    ]


def _multi_step_distribution_series() -> list[DistributionSeries]:
    run = RunMeta(hash="abcdef1234567890", experiment="exp-a", name=None, creation_time=None)
    return [
        DistributionSeries(
            run=run,
            name="empty",
            context={"kind": "empty"},
            points=[],
        ),
        DistributionSeries(
            run=run,
            name="head/gradients/head.0.bias",
            context={"kind": "gradients", "module": "head"},
            points=[
                DistributionPoint(
                    step=300,
                    epoch=0.0,
                    bin_edges=np.array([-1.0, 0.0, 1.0]),
                    weights=np.array([0.0, 2.0]),
                ),
                DistributionPoint(
                    step=600,
                    epoch=0.0,
                    bin_edges=np.array([-1.0, 0.0, 1.0]),
                    weights=np.array([3.0, 0.0]),
                ),
                DistributionPoint(
                    step=900,
                    epoch=0.0,
                    bin_edges=np.array([-1.0, 0.0, 1.0]),
                    weights=np.array([1.0, 4.0]),
                ),
            ],
        ),
    ]


def test_render_distribution_table_includes_tensor_column() -> None:
    output = render_distribution_table(_sample_distribution_series(), no_color=True)

    assert "TENSOR" in output
    assert "weights" in output
    assert "[3, 5]" in output


def test_render_distribution_csv_contains_bin_edges_and_weights() -> None:
    output = render_distribution_csv(_sample_distribution_series())

    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert rows
    assert rows[0]["distribution"] == "weights"
    assert rows[0]["bin_edges"] == "[0.0, 1.0, 2.0]"
    assert rows[0]["weights"] == "[3.0, 5.0]"


def test_render_distribution_json_contains_points() -> None:
    output = render_distribution_json(_sample_distribution_series())
    payload = json.loads(output)

    assert payload
    first = payload[0]
    assert first["distribution"] == "weights"
    assert first["count"] == 2
    assert first["points"][0]["step"] == 10
    assert first["points"][0]["weights"] == [3.0, 5.0]


def test_select_distribution_visual_uses_first_non_empty_series_and_first_point() -> None:
    selection = select_distribution_visual(_multi_step_distribution_series())

    assert selection is not None
    assert selection.selected_index == 1
    assert selection.series.name == "head/gradients/head.0.bias"
    assert selection.resolved_step == 300


def test_select_distribution_visual_returns_none_without_points() -> None:
    series = _multi_step_distribution_series()[:1]
    assert select_distribution_visual(series) is None


def test_select_distribution_visual_resolves_exact_step() -> None:
    selection = select_distribution_visual(_multi_step_distribution_series(), selected_step=600)

    assert selection is not None
    assert selection.resolved_step == 600
    assert not selection.used_nearest_step


def test_select_distribution_visual_resolves_nearest_higher_step() -> None:
    selection = select_distribution_visual(_multi_step_distribution_series(), selected_step=500)

    assert selection is not None
    assert selection.resolved_step == 600


def test_select_distribution_visual_uses_lower_step_for_tie() -> None:
    selection = select_distribution_visual(_multi_step_distribution_series(), selected_step=750)

    assert selection is not None
    assert selection.resolved_step == 600


def test_render_distribution_visual_includes_name_context_histogram_and_heatmap() -> None:
    output = render_distribution_visual(_multi_step_distribution_series(), no_color=True)

    assert "Distributions" in output
    assert "▌ head/gradients/head.0.bias" in output
    assert 'kind="gradients", module="head"' in output
    assert "Histogram" in output
    assert "Step 300" in output
    assert "Heatmap (steps x bins)" in output
    assert "300 |" in output
    assert "Scale: low -> high" in output
    assert "█" in output
    assert "\x1b[" not in output


def test_render_distribution_visual_uses_blue_gradient_color_by_default() -> None:
    output = render_distribution_visual(
        _multi_step_distribution_series(),
        width=80,
        height=14,
    )

    assert "\x1b[" in output
    assert "\x1b[38;2;" in output
    assert "Distributions" in output
    assert "Histogram" in output
    assert "Heatmap (steps x bins)" in output


def test_render_distribution_visual_labels_nearest_step() -> None:
    output = render_distribution_visual(
        _multi_step_distribution_series(),
        selected_step=750,
        no_color=True,
    )

    assert "Step 600" in output
    assert "Requested step 750; showing nearest tracked step 600." in output


def test_render_distribution_visual_handles_single_step_and_all_zero_weights() -> None:
    run = RunMeta(hash="abcdef1234567890", experiment="exp-a", name=None, creation_time=None)
    series = [
        DistributionSeries(
            run=run,
            name="zeros",
            context={},
            points=[
                DistributionPoint(
                    step=1,
                    epoch=None,
                    bin_edges=np.array([0.0, 1.0, 2.0]),
                    weights=np.array([0.0, 0.0]),
                )
            ],
        )
    ]

    output = render_distribution_visual(series, no_color=True)

    assert "zeros" in output
    assert "Step 1" in output
    assert "▁▁" in output
