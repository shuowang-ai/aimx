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
