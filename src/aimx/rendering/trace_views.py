from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import shutil
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from aimx.aim_bridge.metric_stats import DistributionSeries, MetricSeries
from aimx.rendering import colors

_DISTRIBUTION_BLOCKS = "▁▂▃▄▅▆▇█"
_DISTRIBUTION_BLUE_STYLES = (
    "#dbeafe",
    "#bfdbfe",
    "#93c5fd",
    "#60a5fa",
    "#3b82f6",
    "#2563eb",
    "#1d4ed8",
    "#1e40af",
)
_DISTRIBUTION_ZERO_STYLE = "#334155"
_DISTRIBUTION_HEADER_STYLE = "#93c5fd"
_DISTRIBUTION_DIM_STYLE = "#64748b"
_DISTRIBUTION_RULE_STYLE = "#1e3a8a"
_DISTRIBUTION_MARKER_STYLE = "#2563eb bold"
_DISTRIBUTION_SELECTED_STYLE = "bold white"


def _short_hash(h: str) -> str:
    return h[:8]


def _fmt_context(ctx: dict[str, Any]) -> str:
    if not ctx:
        return ""
    return " ".join(f"{k}={v}" for k, v in sorted(ctx.items()))


def _fmt_context_for_visual(ctx: dict[str, Any]) -> str:
    if not ctx:
        return ""
    return ", ".join(f"{k}={json.dumps(v)}" for k, v in sorted(ctx.items()))


def _series_label(series: MetricSeries) -> str:
    parts = [_short_hash(series.run.hash)]
    if series.run.experiment:
        parts.append(series.run.experiment)
    elif series.run.name:
        parts.append(series.run.name)
    parts.append(series.name)
    ctx = _fmt_context(series.context)
    if ctx:
        parts.append(f"[{ctx}]")
    return " · ".join(parts)


def _distribution_series_label(series: DistributionSeries) -> str:
    parts = [_short_hash(series.run.hash)]
    if series.run.experiment:
        parts.append(series.run.experiment)
    elif series.run.name:
        parts.append(series.run.name)
    parts.append(series.name)
    ctx = _fmt_context(series.context)
    if ctx:
        parts.append(f"[{ctx}]")
    return " · ".join(parts)


@dataclass(frozen=True)
class DistributionVisualSelection:
    selected_index: int
    series: DistributionSeries
    point_index: int
    requested_step: int | None
    resolved_step: int

    @property
    def point(self):
        return self.series.points[self.point_index]

    @property
    def used_nearest_step(self) -> bool:
        return self.requested_step is not None and self.requested_step != self.resolved_step


def select_distribution_visual(
    series_list: list[DistributionSeries],
    *,
    selected_step: int | None = None,
) -> DistributionVisualSelection | None:
    """Select the first non-empty distribution and resolve the display step."""
    for selected_index, series in enumerate(series_list):
        if series.count == 0:
            continue
        if selected_step is None:
            return DistributionVisualSelection(
                selected_index=selected_index,
                series=series,
                point_index=0,
                requested_step=None,
                resolved_step=series.points[0].step,
            )

        point_index, point = min(
            enumerate(series.points),
            key=lambda item: (abs(item[1].step - selected_step), item[1].step),
        )
        return DistributionVisualSelection(
            selected_index=selected_index,
            series=series,
            point_index=point_index,
            requested_step=selected_step,
            resolved_step=point.step,
        )
    return None


def _bin_range(point: Any) -> str:
    edges = point.bin_edges.tolist()
    if not edges:
        return ""
    return f"{edges[0]:.6g} .. {edges[-1]:.6g}"


def _compress_values(values: list[float], width: int) -> list[float]:
    if width <= 0 or len(values) <= width:
        return values
    compressed: list[float] = []
    for index in range(width):
        start = index * len(values) // width
        end = (index + 1) * len(values) // width
        bucket = values[start:end] or [values[start]]
        finite = [v for v in bucket if math.isfinite(v)]
        compressed.append(max(finite) if finite else 0.0)
    return compressed


def _intensity_text(values: list[float], *, width: int) -> Text:
    values = _compress_values(values, width)
    text = Text()
    if not values:
        return text
    finite_samples = [float(v) for v in values if math.isfinite(v)]
    max_value = max(finite_samples) if finite_samples else 0.0
    if max_value <= 0:
        text.append(_DISTRIBUTION_BLOCKS[0] * len(values), style=_DISTRIBUTION_ZERO_STYLE)
        return text
    for value in values:
        if not math.isfinite(value) or value <= 0:
            text.append(_DISTRIBUTION_BLOCKS[0], style=_DISTRIBUTION_ZERO_STYLE)
            continue
        scale = float(value) / max_value
        index = round(scale * (len(_DISTRIBUTION_BLOCKS) - 1))
        text.append(_DISTRIBUTION_BLOCKS[index], style=_DISTRIBUTION_BLUE_STYLES[index])
    return text


def _sample_points_for_height(points: list[Any], max_rows: int) -> list[Any]:
    if max_rows <= 0 or len(points) <= max_rows:
        return points
    if max_rows == 1:
        # Evenly-spaced indices use (max_rows - 1) in the denominator; skip when
        # max_rows is 1 and show the latest step as a single representative row.
        return [points[-1]]
    indexes = sorted({round(i * (len(points) - 1) / (max_rows - 1)) for i in range(max_rows)})
    return [points[index] for index in indexes]


def _render_distribution_name_list(
    console: Console,
    series_list: list[DistributionSeries],
    selected_index: int,
) -> None:
    console.print(f"[{_DISTRIBUTION_HEADER_STYLE}]Distributions[/]")
    for index, series in enumerate(series_list):
        label = escape(series.name)
        count = f"{series.count} steps" if series.count != 1 else "1 step"
        if index == selected_index:
            console.print(
                f"[{_DISTRIBUTION_MARKER_STYLE}]▌[/] "
                f"[{_DISTRIBUTION_SELECTED_STYLE}]{label}[/] "
                f"[{_DISTRIBUTION_DIM_STYLE}]({count})[/]"
            )
            ctx = _fmt_context_for_visual(series.context)
            if ctx:
                console.print(f"  [{_DISTRIBUTION_DIM_STYLE}]{escape(ctx)}[/]")
        else:
            console.print(f"  [{_DISTRIBUTION_DIM_STYLE}]{label} ({count})[/]")


def render_distribution_visual(
    series_list: list[DistributionSeries],
    *,
    selected_step: int | None = None,
    width: int | None = None,
    height: int | None = None,
    no_color: bool = False,
) -> str:
    """Render distribution names plus a selected histogram and heatmap."""
    term_width = shutil.get_terminal_size(fallback=(120, 30)).columns
    console_width = width or (120 if no_color else term_width)
    chart_width = max(24, min(96, console_width - 18))
    max_heatmap_rows = max(1, (height - 12) if height is not None else 18)

    buf = io.StringIO()
    console = Console(
        file=buf,
        no_color=no_color,
        color_system=None if no_color else "truecolor",
        force_terminal=not no_color,
        width=console_width,
        highlight=False,
    )

    selection = select_distribution_visual(series_list, selected_step=selected_step)
    if selection is None:
        console.print("No data in the requested step range.")
        return buf.getvalue()

    _render_distribution_name_list(console, series_list, selection.selected_index)
    selected = selection.series
    point = selection.point
    weights = [float(v) for v in point.weights.tolist()]

    console.print()
    console.print(
        f"[{_DISTRIBUTION_HEADER_STYLE}]╭─ Histogram[/] "
        f"[{_DISTRIBUTION_SELECTED_STYLE}]{escape(selected.name)}[/] "
        f"[{_DISTRIBUTION_HEADER_STYLE}]Step {selection.resolved_step}[/]"
    )
    if selection.used_nearest_step:
        console.print(
            f"[{_DISTRIBUTION_DIM_STYLE}]Requested step {selection.requested_step}; "
            f"showing nearest tracked step {selection.resolved_step}.[/]"
        )
    bin_range = _bin_range(point)
    if bin_range:
        console.print(
            f"[{_DISTRIBUTION_DIM_STYLE}]Bins {bin_range}; "
            f"max weight {max(weights) if weights else 0:.6g}[/]"
        )
    console.print(_intensity_text(weights, width=chart_width))
    console.print(f"[{_DISTRIBUTION_RULE_STYLE}]╰{'─' * min(chart_width, console_width - 2)}[/]")

    console.print()
    console.print(f"[{_DISTRIBUTION_HEADER_STYLE}]╭─ Heatmap (steps x bins)[/]")
    selected_points = _sample_points_for_height(selected.points, max_heatmap_rows)
    for heatmap_point in selected_points:
        row = Text(f"{heatmap_point.step:>8} | ", style=_DISTRIBUTION_DIM_STYLE)
        row.append_text(
            _intensity_text(
                [float(v) for v in heatmap_point.weights.tolist()],
                width=chart_width,
            )
        )
        console.print(row)
    if len(selected_points) < len(selected.points):
        console.print(
            f"[{_DISTRIBUTION_DIM_STYLE}]Showing {len(selected_points)} of {len(selected.points)} steps; "
            "use --height to adjust.[/]"
        )
    scale = Text("Scale: ", style=_DISTRIBUTION_DIM_STYLE)
    scale.append("low", style=_DISTRIBUTION_BLUE_STYLES[0])
    scale.append(" -> ", style=_DISTRIBUTION_DIM_STYLE)
    scale.append("high", style=_DISTRIBUTION_BLUE_STYLES[-1])
    console.print(scale)

    return buf.getvalue()


def render_plot(
    series_list: list[MetricSeries],
    *,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """Render time-series curves using plotext and return as a string."""
    import plotext as plt  # noqa: PLC0415

    plt.clt()
    plt.cld()

    term_width = shutil.get_terminal_size(fallback=(120, 30)).columns
    plot_width = width or term_width
    plot_height = height or 25
    plt.plot_size(plot_width, plot_height)

    for series in series_list:
        if series.count == 0:
            continue
        label = _series_label(series)
        x = series.steps.tolist()
        y = series.values.tolist()
        plt.plot(x, y, label=label)

    if series_list:
        first = series_list[0]
        title = first.name if all(s.name == first.name for s in series_list) else "Metrics"
        plt.title(title)
    plt.xlabel("Step")
    plt.ylabel("Value")
    plt.theme("dark")

    output_buf = io.StringIO()
    with contextlib.redirect_stdout(output_buf):
        plt.show()
    return output_buf.getvalue()


def render_trace_table(
    series_list: list[MetricSeries],
    *,
    no_color: bool = False,
) -> str:
    """Render each series as a rich table with step/epoch/value columns."""
    width = 120 if no_color else shutil.get_terminal_size(fallback=(120, 24)).columns
    buf = io.StringIO()
    console = Console(
        file=buf,
        no_color=no_color,
        force_terminal=not no_color,
        width=width,
        highlight=False,
    )

    for series in series_list:
        label = _series_label(series)
        console.print(f"\n[{colors.HEADER}]{label}[/]  [{colors.HEADER}]{series.count} points[/]")

        table = Table(
            show_header=True,
            header_style=colors.HEADER,
            box=None,
            pad_edge=True,
            show_edge=False,
            padding=(0, 1),
        )
        table.add_column("STEP", justify="right")
        table.add_column("EPOCH", justify="right")
        table.add_column("VALUE", justify="right", style=colors.NUMBER_EMPH)

        for i in range(series.count):
            step = int(series.steps[i])
            epoch = f"{series.epochs[i]:.0f}" if series.epochs is not None else "—"
            val = series.values[i]
            val_str = "—" if math.isnan(float(val)) else f"{float(val):.6g}"
            table.add_row(str(step), epoch, val_str)

        console.print(table)

    return buf.getvalue()


def render_csv(series_list: list[MetricSeries]) -> str:
    """Render series data as CSV: run_hash,experiment,metric,context,step,epoch,value."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["run_hash", "experiment", "metric", "context", "step", "epoch", "value"])
    for series in series_list:
        ctx_str = json.dumps(series.context, sort_keys=True)
        for i in range(series.count):
            step = int(series.steps[i])
            epoch = float(series.epochs[i]) if series.epochs is not None else ""
            val = float(series.values[i])
            writer.writerow(
                [
                    series.run.hash,
                    series.run.experiment or series.run.name or "",
                    series.name,
                    ctx_str,
                    step,
                    epoch,
                    val,
                ]
            )
    return buf.getvalue()


def render_trace_json(series_list: list[MetricSeries]) -> str:
    """Render series data as JSON with full value arrays."""
    result: list[dict[str, Any]] = []
    for series in series_list:
        result.append(
            {
                "run": {
                    "hash": series.run.hash,
                    "experiment": series.run.experiment,
                    "name": series.run.name,
                },
                "metric": series.name,
                "context": series.context,
                "count": series.count,
                "steps": series.steps.tolist(),
                "epochs": series.epochs.tolist() if series.epochs is not None else None,
                "values": series.values.tolist(),
            }
        )
    return json.dumps(result)


def _format_tensor(values: list[float], *, limit: int = 12) -> str:
    if len(values) <= limit:
        return "[" + ", ".join(f"{v:.6g}" for v in values) + "]"
    head = ", ".join(f"{v:.6g}" for v in values[:limit])
    return f"[{head}, …] ({len(values)} bins)"


def render_distribution_table(
    series_list: list[DistributionSeries],
    *,
    no_color: bool = False,
) -> str:
    """Render distribution series as a step-indexed tensor table."""
    width = 120 if no_color else shutil.get_terminal_size(fallback=(120, 24)).columns
    buf = io.StringIO()
    console = Console(
        file=buf,
        no_color=no_color,
        force_terminal=not no_color,
        width=width,
        highlight=False,
    )

    for series in series_list:
        label = _distribution_series_label(series)
        console.print(f"\n[{colors.HEADER}]{label}[/]  [{colors.HEADER}]{series.count} points[/]")

        table = Table(
            show_header=True,
            header_style=colors.HEADER,
            box=None,
            pad_edge=True,
            show_edge=False,
            padding=(0, 1),
        )
        table.add_column("STEP", justify="right")
        table.add_column("EPOCH", justify="right")
        table.add_column("TENSOR", justify="left", style=colors.NUMBER_EMPH)

        for point in series.points:
            epoch = f"{point.epoch:.6g}" if point.epoch is not None else "—"
            weights = point.weights.tolist()
            table.add_row(str(point.step), epoch, _format_tensor(weights))

        console.print(table)

    return buf.getvalue()


def render_distribution_csv(series_list: list[DistributionSeries]) -> str:
    """Render distribution rows as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["run_hash", "experiment", "distribution", "context", "step", "epoch", "bin_edges", "weights"]
    )
    for series in series_list:
        ctx_str = json.dumps(series.context, sort_keys=True)
        for point in series.points:
            writer.writerow(
                [
                    series.run.hash,
                    series.run.experiment or series.run.name or "",
                    series.name,
                    ctx_str,
                    point.step,
                    point.epoch if point.epoch is not None else "",
                    json.dumps(point.bin_edges.tolist()),
                    json.dumps(point.weights.tolist()),
                ]
            )
    return buf.getvalue()


def render_distribution_json(series_list: list[DistributionSeries]) -> str:
    """Render distribution rows as JSON."""
    result: list[dict[str, Any]] = []
    for series in series_list:
        result.append(
            {
                "run": {
                    "hash": series.run.hash,
                    "experiment": series.run.experiment,
                    "name": series.run.name,
                },
                "distribution": series.name,
                "context": series.context,
                "count": series.count,
                "points": [
                    {
                        "step": point.step,
                        "epoch": point.epoch,
                        "bin_edges": point.bin_edges.tolist(),
                        "weights": point.weights.tolist(),
                    }
                    for point in series.points
                ],
            }
        )
    return json.dumps(result)
