from __future__ import annotations

import matplotlib.pyplot as plt

from data_generators import generate_rationality_data
from export_utils import export_figure
from style_config import (
    BLUE,
    DARK_GRAY,
    FIGURE_SPECS,
    FONT_SMALL,
    GRAY,
    GREEN,
    LIGHT_GRAY,
    LINE_SECONDARY,
    LINE_THIN,
    ORANGE,
    RED,
    add_panel_label,
    apply_style,
    format_axis,
)


STEM = "fig07_rationality_structural"


def _column_limits(series_by_row):
    low = min(float(item.lower.min()) for item in series_by_row)
    high = max(float(item.upper.max()) for item in series_by_row)
    pad = 0.08 * (high - low)
    return low - pad, high + pad


def make_figure():
    apply_style()
    generated = generate_rationality_data()
    years = generated["years"]
    corpora = generated["corpora"]
    data = generated["data"]
    spec = FIGURE_SPECS[STEM]
    fig, axes = plt.subplots(
        4,
        4,
        figsize=spec.size_in,
        sharex=True,
        gridspec_kw={
            "left": 0.105,
            "right": 0.988,
            "top": 0.91,
            "bottom": 0.095,
            "wspace": 0.22,
            "hspace": 0.20,
        },
    )
    column_titles = [
        "Second principal component",
        "Sentiment",
        "Intuition-related words",
        "Rationality-related words",
    ]
    for col, title in enumerate(column_titles):
        axes[0, col].set_title(title, fontsize=7.5, pad=4)

    pc_limits = _column_limits([data[corpus]["pc2"] for corpus in corpora])
    intuition_limits = _column_limits([data[corpus]["intuition"] for corpus in corpora])
    rational_limits = _column_limits([data[corpus]["rationality"] for corpus in corpora])
    sentiment_limits = (0.23, 0.62)
    letters = iter("abcdefghijklmnop")
    sentiment_colors = {"positive": GREEN, "neutral": BLUE, "negative": RED}

    for row, corpus in enumerate(corpora):
        row_data = data[corpus]
        row_mid = (axes[row, 0].get_position().y0 + axes[row, 0].get_position().y1) / 2
        fig.text(0.018, row_mid, corpus, ha="left", va="center", rotation=90, fontsize=7.0)
        panels = [
            ("pc2", pc_limits),
            ("sentiment", sentiment_limits),
            ("intuition", intuition_limits),
            ("rationality", rational_limits),
        ]
        for col, (kind, ylim) in enumerate(panels):
            ax = axes[row, col]
            letter = next(letters)
            if kind == "sentiment":
                sentiment = row_data["sentiment"]
                for name, color in sentiment_colors.items():
                    ax.plot(
                        years,
                        sentiment[name],
                        color=color,
                        lw=0.80,
                        label=name,
                    )
                if row == 0:
                    ax.legend(
                        frameon=False,
                        loc="upper left",
                        bbox_to_anchor=(0.02, 0.98),
                        borderaxespad=0,
                        ncol=1,
                        handlelength=1.4,
                    )
            else:
                panel = row_data[kind]
                ax.fill_between(years, panel.lower, panel.upper, color=LIGHT_GRAY, alpha=0.28, lw=0)
                ax.plot(years, panel.raw, color=LIGHT_GRAY, lw=LINE_THIN, alpha=0.55)
                ax.plot(years, panel.smooth, color=DARK_GRAY, lw=LINE_SECONDARY)
                ax.axhline(0, color=GRAY, lw=0.45)
            ax.set_xlim(years.min(), years.max())
            ax.set_ylim(*ylim)
            ax.set_xticks([1800, 1850, 1900, 1950, 2000])
            if row < 3:
                ax.tick_params(labelbottom=False)
            else:
                ax.set_xlabel("Year")
            if col > 0:
                ax.tick_params(labelleft=False)
            ax.grid(axis="y", color="#000000", alpha=0.08, lw=0.45)
            format_axis(ax)
            add_panel_label(ax, letter, x=-0.18, y=1.03)
    return fig


def main():
    result = export_figure(make_figure(), STEM)
    print(result)


if __name__ == "__main__":
    main()

