from __future__ import annotations

import matplotlib.pyplot as plt

from data_generators import generate_alphago_data
from export_utils import export_figure
from style_config import (
    BLUE,
    DARK_GRAY,
    FIGURE_SPECS,
    FONT_ANNOTATION,
    LINE_MAIN,
    LINE_SECONDARY,
    MARKER_SIZE,
    ORANGE,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig02_alphago_zero_structural"


def make_figure():
    apply_style()
    df = generate_alphago_data()
    spec = FIGURE_SPECS[STEM]
    fig, axes = plt.subplots(
        1,
        3,
        figsize=spec.size_in,
        sharex=True,
        gridspec_kw={
            "left": 0.065,
            "right": 0.985,
            "top": 0.90,
            "bottom": 0.18,
            "wspace": 0.36,
            "width_ratios": [1, 1, 1],
        },
    )
    colors = {"Reinforcement learning": BLUE, "Supervised learning": ORANGE}
    metrics = [
        ("elo", "Elo rating", "a"),
        ("move_accuracy", "Professional move accuracy", "b"),
        ("value_mse", "Outcome prediction MSE", "c"),
    ]
    for ax, (metric, ylabel, letter) in zip(axes, metrics):
        for variant, group in df.groupby("variant", sort=False):
            ax.plot(
                group["hour"],
                group[metric],
                color=colors[variant],
                marker="o" if metric == "elo" else None,
                ms=MARKER_SIZE if metric == "elo" else 0,
                lw=LINE_MAIN if variant.startswith("Reinforcement") else LINE_SECONDARY,
                label=variant,
            )
        ax.set_xlabel("Training time / hours")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, 72)
        ax.set_xticks([0, 15, 30, 45, 60, 72])
        ax.grid(axis="y", color="#000000", alpha=0.10, lw=0.45)
        format_axis(ax)
        add_panel_label(ax, letter)
    baseline = 3700
    axes[0].axhline(baseline, color=DARK_GRAY, lw=0.65, ls="--")
    axes[0].text(58, baseline + 160, "external baseline", fontsize=FONT_ANNOTATION, color=DARK_GRAY)
    axes[0].legend(frameon=False, loc="lower right", handlelength=1.5)
    axes[1].set_ylim(0.20, 0.56)
    axes[1].text(48, 0.286, "self-play\npolicy", color=BLUE, fontsize=FONT_ANNOTATION)
    axes[1].text(42, 0.535, "supervised\npolicy", color=ORANGE, fontsize=FONT_ANNOTATION)
    axes[2].set_ylim(0.075, 0.30)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()

