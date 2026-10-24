from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

from data_generators import generate_graphcast_data
from export_utils import export_figure
from style_config import (
    BLUE,
    DARK_GRAY,
    FIGURE_SPECS,
    FONT_TICK,
    GRAY,
    LINE_MAIN,
    LINE_SECONDARY,
    MARKER_SIZE,
    ORANGE,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig01_graphcast_structural"


def make_figure():
    apply_style()
    data = generate_graphcast_data()
    rmse = data["rmse"]
    acc = data["acc"]
    heatmap = data["heatmap"]
    spec = FIGURE_SPECS[STEM]
    fig = plt.figure(figsize=spec.size_in)
    gs = fig.add_gridspec(
        1,
        5,
        width_ratios=[1.0, 1.0, 1.05, 1.55, 0.06],
        left=0.062,
        right=0.94,
        top=0.90,
        bottom=0.17,
        wspace=0.42,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[0, 2])
    ax_d = fig.add_subplot(gs[0, 3])
    cax = fig.add_subplot(gs[0, 4])

    for column, color, label, lw in [
        ("GraphCast", BLUE, "GraphCast", LINE_MAIN),
        ("Reference", ORANGE, "Reference", LINE_SECONDARY),
    ]:
        y = rmse[column].to_numpy()
        ci = rmse[f"{column}_ci"].to_numpy()
        ax_a.plot(rmse["day"], y, color=color, lw=lw, label=label)
        ax_a.fill_between(rmse["day"], y - ci, y + ci, color=color, alpha=0.10, lw=0)
    ax_a.set_xlabel("Lead time / days")
    ax_a.set_ylabel("RMSE")
    ax_a.set_xticks([1, 3, 5, 7, 10])
    ax_a.legend(frameon=False, loc="upper left", handlelength=1.6)
    format_axis(ax_a)
    add_panel_label(ax_a, "a")

    ax_b.axhline(0, color=GRAY, lw=0.55)
    ax_b.plot(
        rmse["day"],
        rmse["relative_diff"],
        color=DARK_GRAY,
        marker="o",
        ms=MARKER_SIZE,
        lw=LINE_SECONDARY,
    )
    ax_b.set_xlabel("Lead time / days")
    ax_b.set_ylabel("Relative RMSE difference")
    ax_b.set_xticks([1, 3, 5, 7, 10])
    format_axis(ax_b)
    add_panel_label(ax_b, "b")

    for column, color, label, lw in [
        ("GraphCast", BLUE, "GraphCast", LINE_MAIN),
        ("Reference", ORANGE, "Reference", LINE_SECONDARY),
    ]:
        ax_c.plot(acc["day"], acc[column], color=color, lw=lw, label=label)
    ax_c.set_xlabel("Lead time / days")
    ax_c.set_ylabel("ACC")
    ax_c.set_xticks([1, 3, 5, 7, 10])
    ax_c.set_ylim(0.94, 1.002)
    format_axis(ax_c)
    add_panel_label(ax_c, "c")

    variables = ["u", "v", "z", "t", "q", "t2m", "u10", "v10", "msl"]
    matrix = (
        heatmap.pivot_table(index="variable", columns="day", values="skill")
        .loc[variables]
        .to_numpy()
    )
    im = ax_d.imshow(
        matrix,
        aspect="auto",
        cmap="RdBu_r",
        norm=TwoSlopeNorm(vmin=-0.18, vcenter=0.0, vmax=0.18),
        interpolation="nearest",
    )
    ax_d.set_yticks(np.arange(len(variables)))
    ax_d.set_yticklabels(variables)
    ax_d.set_xticks([0, 2, 4, 6, 9])
    ax_d.set_xticklabels([1, 3, 5, 7, 10])
    ax_d.set_xlabel("Lead time / days")
    ax_d.tick_params(axis="both", direction="out", width=0.6, length=2.8)
    for spine in ax_d.spines.values():
        spine.set_linewidth(0.6)
    add_panel_label(ax_d, "d", x=-0.11)
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_ticks([-0.18, -0.09, 0, 0.09, 0.18])
    cbar.ax.tick_params(labelsize=FONT_TICK, width=0.6, length=2.5)
    cbar.ax.set_title("Relative RMSE\nskill", fontsize=FONT_TICK, pad=4)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()
