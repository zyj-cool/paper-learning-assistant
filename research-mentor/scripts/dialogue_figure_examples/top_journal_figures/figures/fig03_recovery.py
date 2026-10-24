from __future__ import annotations

import matplotlib.pyplot as plt

from data_generators import at_risk_counts, generate_recovery_patient_data, km_estimate
from export_utils import export_figure
from style_config import (
    BLUE,
    ORANGE,
    FIGURE_SPECS,
    FONT_SMALL,
    LINE_MAIN,
    LINE_SECONDARY,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig03_recovery_structural"
TIMES = [0, 7, 14, 21, 28]


def _draw_risk_table(ax, panel_df) -> None:
    colors = {"Dexamethasone": BLUE, "Usual care": ORANGE}
    counts = at_risk_counts(panel_df, TIMES)
    ax.set_xlim(0, 28)
    ax.set_ylim(-0.42, 1.52)
    ax.set_xticks(TIMES)
    ax.set_yticks([])
    ax.tick_params(direction="out", width=0.6, length=2.8, pad=1.2, labelsize=FONT_SMALL)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.grid(False)
    label_transform = ax.get_yaxis_transform()
    ax.text(0, 1.26, "Number at risk", ha="left", va="center", fontsize=FONT_SMALL)
    for row, treatment in enumerate(["Dexamethasone", "Usual care"]):
        y = 0.74 - row * 0.58
        ax.text(
            -0.070,
            y,
            treatment,
            ha="right",
            va="center",
            fontsize=FONT_SMALL,
            color=colors[treatment],
            transform=label_transform,
            clip_on=False,
        )
        for time, count in zip(TIMES, counts[treatment]):
            ax.text(time, y, f"{count}", ha="center", va="center", fontsize=FONT_SMALL)


def make_figure():
    apply_style()
    df = generate_recovery_patient_data()
    spec = FIGURE_SPECS[STEM]
    fig = plt.figure(figsize=spec.size_in)
    outer = fig.add_gridspec(
        2,
        2,
        left=0.115,
        right=0.985,
        top=0.89,
        bottom=0.085,
        wspace=0.46,
        hspace=0.62,
    )
    panels = [
        ("All patients", None, "a"),
        ("Invasive mechanical ventilation", "Invasive mechanical ventilation", "b"),
        ("Oxygen only", "Oxygen only", "c"),
        ("No respiratory support", "No respiratory support", "d"),
    ]
    colors = {"Dexamethasone": BLUE, "Usual care": ORANGE}
    handles = []
    labels = []
    for idx, (title, subgroup, letter) in enumerate(panels):
        row = idx // 2
        col = idx % 2
        inner = outer[row, col].subgridspec(2, 1, height_ratios=[4.0, 1.15], hspace=0.50)
        ax = fig.add_subplot(inner[0])
        risk_ax = fig.add_subplot(inner[1], sharex=ax)
        panel_df = df if subgroup is None else df.query("subgroup == @subgroup")
        for treatment, group in panel_df.groupby("treatment_group", sort=False):
            curve = km_estimate(
                group["observed_time"].to_numpy(),
                group["event_indicator"].to_numpy(),
                max_time=28,
            )
            line = ax.plot(
                curve["time"],
                curve["mortality"],
                drawstyle="steps-post",
                color=colors[treatment],
                lw=LINE_MAIN if treatment == "Dexamethasone" else LINE_SECONDARY,
                label=treatment,
            )[0]
            if idx == 0:
                handles.append(line)
                labels.append(treatment)
        ax.set_title(title, fontsize=8.0, pad=3)
        ax.set_xlim(0, 28)
        ax.set_ylim(0, 0.50)
        ax.set_xticks(TIMES)
        ax.set_xlabel("Days since randomization")
        if col == 0:
            ax.set_ylabel("Cumulative mortality")
        else:
            ax.set_ylabel("")
        ax.grid(axis="y", color="#000000", alpha=0.10, lw=0.5)
        format_axis(ax)
        add_panel_label(ax, letter, x=-0.12 if col == 0 else -0.13)
        _draw_risk_table(risk_ax, panel_df)
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.53, 0.982),
        ncol=2,
        frameon=False,
        handlelength=2.6,
        columnspacing=1.8,
    )
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()
