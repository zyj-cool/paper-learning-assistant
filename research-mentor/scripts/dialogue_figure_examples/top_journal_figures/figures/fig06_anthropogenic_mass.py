from __future__ import annotations

import matplotlib.pyplot as plt

from data_generators import generate_anthropogenic_mass_data
from export_utils import export_figure
from style_config import (
    BLUE,
    DARK_GRAY,
    FIGURE_SPECS,
    FONT_ANNOTATION,
    GOLD,
    GRAY,
    GREEN,
    LINE_MAIN,
    LINE_THIN,
    ORANGE,
    PURPLE,
    RED,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig06_anthropogenic_mass_structural"


def make_figure():
    apply_style()
    df, cross = generate_anthropogenic_mass_data()
    spec = FIGURE_SPECS[STEM]
    fig, ax = plt.subplots(figsize=spec.size_in)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.95, bottom=0.12)
    categories = ["Concrete", "Aggregates", "Bricks", "Asphalt", "Metals", "Other"]
    colors = [PURPLE, BLUE, GOLD, GRAY, RED, ORANGE]
    total = df[categories].sum(axis=1)
    ax.axvspan(2015, 2025, color="#E6E6E6", alpha=0.72, zorder=0)
    ax.axvline(2015, color=DARK_GRAY, lw=LINE_THIN, ls="--", zorder=1)
    ax.stackplot(
        df["year"],
        *[df[col] for col in categories],
        labels=categories,
        colors=colors,
        linewidth=0,
        alpha=0.90,
    )
    ax.fill_between(df["year"], df["biomass_low"], df["biomass_high"], color=GREEN, alpha=0.18, lw=0)
    ax.plot(df["year"], df["biomass_mean"], color=GREEN, lw=LINE_MAIN, label="Living biomass")
    cross_year, cross_mass = cross
    ax.scatter([cross_year], [cross_mass], color=DARK_GRAY, s=10, zorder=4)
    ax.annotate(
        "Intersection approximately 2020",
        xy=(cross_year, cross_mass),
        xytext=(cross_year - 28, cross_mass + 0.08),
        arrowprops={"arrowstyle": "->", "lw": 0.6, "color": DARK_GRAY},
        fontsize=FONT_ANNOTATION,
        ha="left",
        va="center",
    )
    ax.text(2020, ax.get_ylim()[1] * 0.93, "extrapolated", ha="center", va="top", fontsize=FONT_ANNOTATION, color=DARK_GRAY)
    ax.set_xlim(1900, 2025)
    ax.set_ylim(0, max(float(total.max()), float(df["biomass_high"].max())) * 1.08)
    ax.set_xlabel("Year")
    ax.set_ylabel("Dry mass (Tt)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        frameon=False,
        loc="upper left",
        ncol=4,
        handlelength=1.0,
        columnspacing=0.9,
        borderaxespad=0.2,
    )
    format_axis(ax)
    add_panel_label(ax, "a", x=-0.055, y=1.01)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()

