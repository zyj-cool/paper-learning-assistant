from __future__ import annotations

import matplotlib.pyplot as plt

from data_generators import generate_step5_data
from export_utils import export_figure
from style_config import (
    BLUE,
    CAP_SIZE,
    ERRORBAR_WIDTH,
    FIGURE_SPECS,
    FONT_ANNOTATION,
    GRAY,
    LINE_MAIN,
    LINE_SECONDARY,
    MARKER_SIZE,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig04_step5_structural"


def make_figure():
    apply_style()
    generated = generate_step5_data()
    trajectory = generated["trajectory"]
    endpoint = generated["endpoint"]
    spec = FIGURE_SPECS[STEM]
    fig = plt.figure(figsize=spec.size_in)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[3.2, 1.0],
        left=0.07,
        right=0.985,
        top=0.89,
        bottom=0.18,
        wspace=0.32,
    )
    ax_line = fig.add_subplot(gs[0, 0])
    ax_bar = fig.add_subplot(gs[0, 1])
    colors = {"Semaglutide": BLUE, "Placebo": GRAY}
    markers = {"Semaglutide": "o", "Placebo": "s"}
    for treatment, group in trajectory.groupby("treatment", sort=False):
        group = group.sort_values("week")
        ax_line.errorbar(
            group["week"],
            group["mean_change_pct"],
            yerr=group["sem"],
            color=colors[treatment],
            lw=LINE_MAIN if treatment == "Semaglutide" else LINE_SECONDARY,
            marker=markers[treatment],
            ms=MARKER_SIZE,
            elinewidth=ERRORBAR_WIDTH,
            capsize=CAP_SIZE,
            label=treatment,
        )
    ax_line.axhline(0, color="#444444", lw=0.55)
    ax_line.set_xlabel("Week")
    ax_line.set_ylabel("Change in body weight from baseline (%)")
    ax_line.set_xlim(-2, 106)
    ax_line.set_ylim(-17.5, 1.5)
    ax_line.set_xticks([0, 20, 40, 60, 80, 104])
    ax_line.legend(frameon=False, loc="lower left", handlelength=1.5)
    ax_line.grid(axis="y", color="#000000", alpha=0.10, lw=0.45)
    ax_line.text(
        63,
        -8.3,
        "Week 104 ETD: -12.6 percentage points\n95% CI: -13.5 to -11.6",
        ha="left",
        va="center",
        fontsize=FONT_ANNOTATION,
    )
    format_axis(ax_line)
    add_panel_label(ax_line, "a", x=-0.09)

    bars = ax_bar.bar(
        [0, 1],
        endpoint["percent"],
        color=[BLUE, GRAY],
        width=0.55,
    )
    ax_bar.set_xticks([0, 1])
    ax_bar.set_xticklabels(endpoint["treatment"], rotation=28, ha="right")
    ax_bar.set_ylim(0, 100)
    ax_bar.set_yticks([0, 20, 40, 60, 80, 100])
    ax_bar.set_ylabel("Participants with >=5% weight loss (%)")
    for bar, value in zip(bars, endpoint["percent"]):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, value + 2.6, f"{value:.1f}%", ha="center", fontsize=FONT_ANNOTATION)
    ax_bar.text(0.5, 94, "OR 5.0\n95% CI 3.0-8.4", ha="center", fontsize=FONT_ANNOTATION)
    ax_bar.grid(axis="y", color="#000000", alpha=0.10, lw=0.45)
    format_axis(ax_bar)
    add_panel_label(ax_bar, "b", x=-0.22)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()
