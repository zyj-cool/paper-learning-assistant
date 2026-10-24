from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from data_generators import generate_alphafold_data
from export_utils import export_figure
from style_config import (
    BLUE,
    FIGURE_SPECS,
    GRAY,
    LIGHT_GRAY,
    LINE_THIN,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig05_alphafold_structural"


def make_figure():
    apply_style()
    summary = generate_alphafold_data().sort_values("median_score", ascending=False).reset_index(drop=True)
    spec = FIGURE_SPECS[STEM]
    fig, ax = plt.subplots(figsize=spec.size_in)
    fig.subplots_adjust(left=0.34, right=0.98, top=0.97, bottom=0.105)
    y = np.arange(len(summary))
    for pos, row in zip(y, summary.itertuples()):
        color = BLUE if row.highlight else GRAY
        marker_size = 4.2 if row.highlight else 3.2
        elinewidth = 1.0 if row.highlight else 0.75
        ax.errorbar(
            row.median_score,
            pos,
            xerr=[
                [row.median_score - row.ci_low],
                [row.ci_high - row.median_score],
            ],
            fmt="o",
            color=color,
            ms=marker_size,
            elinewidth=elinewidth,
            capsize=1.8,
            lw=elinewidth,
        )
    for ref in [60, 75, 90]:
        ax.axvline(ref, color=LIGHT_GRAY, lw=LINE_THIN, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(summary["group_name"])
    ax.invert_yaxis()
    ax.set_xlabel("Median GDT_TS with bootstrap interval")
    ax.set_ylabel("CASP group")
    ax.set_xlim(40, 95)
    ax.set_xticks([40, 55, 70, 85, 95])
    format_axis(ax)
    add_panel_label(ax, "a", x=-0.48, y=1.01)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()

